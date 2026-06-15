from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import ReadSessionFactory, WriteSessionFactory
from app.domain.models import ClimateIndex, WeatherForecast, WeatherSnapshot


class MariaDbWeatherSnapshotWriter:
    def __init__(
        self,
        session_factory: Callable[..., AsyncSession] = WriteSessionFactory,
        batch_size: int | None = None,
        retention: int | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.batch_size = batch_size or settings.weather_database_batch_size
        self.retention = retention or settings.weather_snapshot_retention
        self.progress_callback = progress_callback

    async def save(self, snapshot: dict[str, Any]) -> int:
        snapshot_id = await self._create_snapshot(snapshot)
        try:
            forecast_rows = self._build_forecast_rows(snapshot_id, snapshot)
            climate_rows = self._build_climate_rows(snapshot_id, snapshot)
            await self._insert_batches(
                WeatherForecast,
                forecast_rows,
                "동네예보",
            )
            await self._insert_batches(
                ClimateIndex,
                climate_rows,
                "관광기후지수",
            )
            await self._validate_counts(
                snapshot_id,
                len(forecast_rows),
                len(climate_rows),
            )
            await self._activate(
                snapshot_id,
                len(forecast_rows),
                len(climate_rows),
            )
            await self._delete_expired_snapshots()
            return snapshot_id
        except Exception:
            await self._mark_failed(snapshot_id)
            raise

    async def _create_snapshot(self, snapshot: dict[str, Any]) -> int:
        async with self.session_factory() as session:
            record = WeatherSnapshot(
                base_time=snapshot["base_time"],
                collected_at=datetime.fromisoformat(snapshot["collected_at"]),
                status="COLLECTING",
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id

    async def _insert_batches(
        self,
        model,
        rows: list[dict[str, Any]],
        label: str,
    ) -> None:
        for offset in range(0, len(rows), self.batch_size):
            async with self.session_factory() as session:
                await session.execute(
                    insert(model),
                    rows[offset : offset + self.batch_size],
                )
                await session.commit()
            if self.progress_callback is not None:
                self.progress_callback(
                    label,
                    min(offset + self.batch_size, len(rows)),
                    len(rows),
                )

    async def _validate_counts(
        self,
        snapshot_id: int,
        expected_forecasts: int,
        expected_climate_indices: int,
    ) -> None:
        async with self.session_factory() as session:
            forecast_count = await session.scalar(
                select(func.count())
                .select_from(WeatherForecast)
                .where(WeatherForecast.snapshot_id == snapshot_id)
            )
            climate_count = await session.scalar(
                select(func.count())
                .select_from(ClimateIndex)
                .where(ClimateIndex.snapshot_id == snapshot_id)
            )
        if (
            forecast_count != expected_forecasts
            or climate_count != expected_climate_indices
        ):
            raise RuntimeError(
                "Weather snapshot row count validation failed: "
                f"forecasts={forecast_count}/{expected_forecasts}, "
                f"climate_indices={climate_count}/{expected_climate_indices}"
            )

    async def _activate(
        self,
        snapshot_id: int,
        forecast_count: int,
        climate_index_count: int,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(WeatherSnapshot)
                    .where(WeatherSnapshot.status == "ACTIVE")
                    .values(status="ARCHIVED")
                )
                await session.execute(
                    update(WeatherSnapshot)
                    .where(WeatherSnapshot.id == snapshot_id)
                    .values(
                        status="ACTIVE",
                        forecast_count=forecast_count,
                        climate_index_count=climate_index_count,
                    )
                )

    async def _mark_failed(self, snapshot_id: int) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(WeatherSnapshot)
                .where(WeatherSnapshot.id == snapshot_id)
                .values(status="FAILED")
            )
            await session.commit()

    async def _delete_expired_snapshots(self) -> None:
        async with self.session_factory() as session:
            retained_ids = list(
                (
                    await session.scalars(
                        select(WeatherSnapshot.id)
                        .where(WeatherSnapshot.status == "ARCHIVED")
                        .order_by(WeatherSnapshot.collected_at.desc())
                        .limit(self.retention)
                    )
                ).all()
            )
            expired_ids = list(
                (
                    await session.scalars(
                        select(WeatherSnapshot.id).where(
                            WeatherSnapshot.status.in_(["ARCHIVED", "FAILED"]),
                            WeatherSnapshot.id.not_in(retained_ids),
                        )
                    )
                ).all()
            )
            if not expired_ids:
                return
            await session.execute(
                delete(WeatherForecast).where(
                    WeatherForecast.snapshot_id.in_(expired_ids)
                )
            )
            await session.execute(
                delete(ClimateIndex).where(
                    ClimateIndex.snapshot_id.in_(expired_ids)
                )
            )
            await session.execute(
                delete(WeatherSnapshot).where(
                    WeatherSnapshot.id.in_(expired_ids)
                )
            )
            await session.commit()

    @staticmethod
    def _build_forecast_rows(
        snapshot_id: int,
        snapshot: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for course_id, forecasts in snapshot["village_forecasts"].items():
            for item in forecasts:
                rows.append(
                    {
                        "snapshot_id": snapshot_id,
                        "course_id": int(course_id),
                        "spot_area_id": item["spot_area_id"],
                        "forecast_at": datetime.fromisoformat(
                            item["forecast_at"]
                        ),
                        "spot_area_name": item["spot_area_name"],
                        "spot_name": item["spot_name"],
                        "themes": item.get("themes", []),
                        "temperature": Decimal(str(item["temperature"])),
                        "wind_direction": item["wind_direction"],
                        "wind_speed": Decimal(str(item["wind_speed"])),
                        "sky": item["sky"],
                        "humidity": item["humidity"],
                        "rain_probability": item["rain_probability"],
                    }
                )
        return rows

    @staticmethod
    def _build_climate_rows(
        snapshot_id: int,
        snapshot: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "snapshot_id": snapshot_id,
                "city_area_id": city_area_id,
                "score": Decimal(str(item["score"])),
                "grade": item["grade"],
            }
            for city_area_id, item in snapshot["climate_indices"].items()
        ]


async def load_active_database_snapshot() -> dict[str, Any]:
    async with WriteSessionFactory() as session:
        active = await session.scalar(
            select(WeatherSnapshot)
            .where(WeatherSnapshot.status == "ACTIVE")
            .order_by(WeatherSnapshot.collected_at.desc())
            .limit(1)
        )
        if active is None:
            return {
                "course_metadata": {},
                "village_forecasts": {},
                "climate_indices": {},
            }
        forecasts = list(
            (
                await session.scalars(
                    select(WeatherForecast)
                    .where(WeatherForecast.snapshot_id == active.id)
                    .order_by(
                        WeatherForecast.course_id,
                        WeatherForecast.forecast_at,
                        WeatherForecast.spot_area_id,
                    )
                )
            ).all()
        )
        climate_indices = list(
            (
                await session.scalars(
                    select(ClimateIndex).where(
                        ClimateIndex.snapshot_id == active.id
                    )
                )
            ).all()
        )

    grouped_forecasts: dict[str, list[dict[str, Any]]] = {}
    for record in forecasts:
        grouped_forecasts.setdefault(str(record.course_id), []).append(
            {
                "forecast_at": record.forecast_at.strftime("%Y-%m-%d %H:%M"),
                "themes": record.themes,
                "spot_area_id": record.spot_area_id,
                "spot_area_name": record.spot_area_name,
                "spot_name": record.spot_name,
                "temperature": float(record.temperature),
                "wind_direction": record.wind_direction,
                "wind_speed": float(record.wind_speed),
                "sky": record.sky,
                "humidity": record.humidity,
                "rain_probability": record.rain_probability,
            }
        )
    return {
        "base_time": active.base_time,
        "collected_at": active.collected_at.isoformat(),
        "course_metadata": {},
        "village_forecasts": grouped_forecasts,
        "climate_indices": {
            item.city_area_id: {
                "score": float(item.score),
                "grade": item.grade,
            }
            for item in climate_indices
        },
    }


class DatabaseWeatherClient:
    async def resolve_base_time(self, suggested_base_time: str) -> str:
        async with ReadSessionFactory() as session:
            base_time = await session.scalar(
                select(WeatherSnapshot.base_time)
                .where(WeatherSnapshot.status == "ACTIVE")
                .order_by(WeatherSnapshot.collected_at.desc())
                .limit(1)
            )
        return base_time or suggested_base_time

    async def get_village_forecast(
        self,
        course_id: int,
        base_time: str,
    ) -> list[dict[str, Any]]:
        async with ReadSessionFactory() as session:
            snapshot_id = await self._active_snapshot_id(session)
            records = list(
                (
                    await session.scalars(
                        select(WeatherForecast)
                        .where(
                            WeatherForecast.snapshot_id == snapshot_id,
                            WeatherForecast.course_id == course_id,
                        )
                        .order_by(
                            WeatherForecast.forecast_at,
                            WeatherForecast.spot_area_id,
                        )
                    )
                ).all()
            )
        if not records:
            self._raise_missing("Village forecast", str(course_id))
        return [
            {
                "forecast_at": record.forecast_at.strftime("%Y-%m-%d %H:%M"),
                "themes": record.themes,
                "spot_area_id": record.spot_area_id,
                "spot_area_name": record.spot_area_name,
                "spot_name": record.spot_name,
                "temperature": float(record.temperature),
                "wind_direction": record.wind_direction,
                "wind_speed": float(record.wind_speed),
                "sky": record.sky,
                "humidity": record.humidity,
                "rain_probability": record.rain_probability,
            }
            for record in records
        ]

    async def get_climate_index(
        self,
        city_area_id: str,
        base_time: str,
    ) -> dict[str, float | str]:
        async with ReadSessionFactory() as session:
            snapshot_id = await self._active_snapshot_id(session)
            record = await session.scalar(
                select(ClimateIndex).where(
                    ClimateIndex.snapshot_id == snapshot_id,
                    ClimateIndex.city_area_id == city_area_id,
                )
            )
        if record is None:
            self._raise_missing("Climate index", city_area_id)
        return {"score": float(record.score), "grade": record.grade}

    @staticmethod
    async def _active_snapshot_id(session: AsyncSession) -> int:
        snapshot_id = await session.scalar(
            select(WeatherSnapshot.id)
            .where(WeatherSnapshot.status == "ACTIVE")
            .order_by(WeatherSnapshot.collected_at.desc())
            .limit(1)
        )
        if snapshot_id is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Active weather snapshot is not available",
            )
        return snapshot_id

    @staticmethod
    def _raise_missing(data_name: str, key: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{data_name} is missing from active snapshot: {key}",
        )


database_weather_client = DatabaseWeatherClient()
