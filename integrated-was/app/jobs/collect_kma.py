import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.infrastructure.kma_client import kma_client
from app.infrastructure.mock_store import mock_store
from app.utils.weather import get_closest_kma_base_time

KST = ZoneInfo("Asia/Seoul")


def _read_existing_snapshot(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "course_metadata": {},
            "village_forecasts": {},
            "climate_indices": {},
        }


async def _with_retry(operation_name: str, operation):
    last_error: Exception | None = None
    for attempt in range(1, settings.kma_collection_retries + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if attempt < settings.kma_collection_retries:
                await asyncio.sleep(settings.kma_collection_retry_seconds)
    raise RuntimeError(
        f"{operation_name} failed after "
        f"{settings.kma_collection_retries} attempts"
    ) from last_error


async def collect_snapshot() -> Path:
    if not settings.kma_service_key:
        raise RuntimeError("KMA_SERVICE_KEY is not configured")

    base_time = get_closest_kma_base_time(
        publication_delay_minutes=10
    )
    snapshot_path = Path(settings.kma_snapshot_path)
    existing = _read_existing_snapshot(snapshot_path)
    course_metadata = dict(existing.get("course_metadata", {}))
    village_forecasts = (
        dict(existing.get("village_forecasts", {}))
        if settings.kma_course_limit > 0
        else {}
    )
    climate_indices = dict(existing.get("climate_indices", {}))

    courses = sorted(
        mock_store.courses.values(),
        key=lambda course: course.kma_course_id,
    )
    if settings.kma_course_limit > 0:
        courses = courses[: settings.kma_course_limit]
    semaphore = asyncio.Semaphore(settings.kma_collection_concurrency)

    async def collect_course(course):
        async with semaphore:
            return await _with_retry(
                f"village forecast for course {course.kma_course_id}",
                lambda: kma_client.get_village_forecast(
                    course.kma_course_id,
                    base_time,
                ),
            )

    forecast_results = await asyncio.gather(
        *[collect_course(course) for course in courses],
        return_exceptions=True,
    )
    failed_course_ids: list[int] = []
    for course, result in zip(courses, forecast_results, strict=True):
        if isinstance(result, Exception):
            failed_course_ids.append(course.kma_course_id)
            continue
        first = result[0] if result else {}
        official_name = first.get("course_name")
        official_location = first.get("course_area_name")
        course_metadata[str(course.kma_course_id)] = {
            "name": official_name or course.name,
            "location": official_location or course.location,
            "spot_count": course.spot_count,
            "themes": course.themes,
        }
        village_forecasts[str(course.kma_course_id)] = [
            {
                key: value
                for key, value in forecast.items()
                if key not in {"course_name", "course_area_name"}
            }
            for forecast in result
        ]

    if failed_course_ids:
        print(
            "warning: village forecast unavailable for "
            f"{len(failed_course_ids)} courses: "
            + ",".join(map(str, failed_course_ids))
        )

    city_area_ids = {
        course.city_area_id
        for course in mock_store.courses.values()
        if course.city_area_id
    }
    climate_results = await asyncio.gather(
        *[
            _with_retry(
                f"climate index for area {city_area_id}",
                lambda area_id=city_area_id: (
                    kma_client.get_climate_index(area_id, base_time)
                ),
            )
            for city_area_id in city_area_ids
        ],
        return_exceptions=True,
    )
    for city_area_id, result in zip(
        city_area_ids,
        climate_results,
        strict=True,
    ):
        if isinstance(result, Exception):
            # Climate index publication can differ from village forecasts.
            print(f"warning: {result}")
            continue
        climate_indices[city_area_id] = result

    if not village_forecasts:
        raise RuntimeError("No village forecast data was collected")

    snapshot = {
        "base_time": base_time,
        "collected_at": datetime.now(KST).isoformat(),
        "course_metadata": course_metadata,
        "village_forecasts": village_forecasts,
        "climate_indices": climate_indices,
    }
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = snapshot_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_path, snapshot_path)
    return snapshot_path


def main() -> None:
    snapshot_path = asyncio.run(collect_snapshot())
    print(f"KMA snapshot updated: {snapshot_path}")


if __name__ == "__main__":
    main()
