import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


class SnapshotWeatherClient:
    def __init__(self, snapshot_path: str | None = None) -> None:
        self.snapshot_path = Path(snapshot_path or settings.kma_snapshot_path)
        self._modified_at_ns: int | None = None
        self._snapshot: dict[str, Any] | None = None

    async def resolve_base_time(self, suggested_base_time: str) -> str:
        return self._load().get("base_time", suggested_base_time)

    async def get_village_forecast(
        self,
        course_id: int,
        base_time: str,
    ) -> list[dict[str, Any]]:
        snapshot = self._load()
        forecast = snapshot.get("village_forecasts", {}).get(str(course_id))
        if forecast is None:
            self._raise_missing("Village forecast", str(course_id))
        if not isinstance(forecast, list):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "KMA snapshot uses the old single-item format. "
                    "Run `python -m app.jobs.collect_kma` again."
                ),
            )
        return forecast

    async def get_climate_index(
        self,
        city_area_id: str,
        base_time: str,
    ) -> dict[str, float | str]:
        snapshot = self._load()
        climate_index = snapshot.get("climate_indices", {}).get(city_area_id)
        if climate_index is None:
            self._raise_missing("Climate index", city_area_id)
        return climate_index

    def _load(self) -> dict[str, Any]:
        try:
            modified_at_ns = self.snapshot_path.stat().st_mtime_ns
            if (
                self._snapshot is None
                or self._modified_at_ns != modified_at_ns
            ):
                self._snapshot = json.loads(
                    self.snapshot_path.read_text(encoding="utf-8")
                )
                self._modified_at_ns = modified_at_ns
            return self._snapshot
        except (OSError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "KMA snapshot is unavailable. Run "
                    "`python -m app.jobs.collect_kma` first."
                ),
            ) from exc

    @staticmethod
    def _raise_missing(data_name: str, key: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{data_name} is missing from snapshot: {key}",
        )


snapshot_weather_client = SnapshotWeatherClient()
