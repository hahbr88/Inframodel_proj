import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import initialize_database
from app.infrastructure.database_weather import (
    MariaDbWeatherSnapshotWriter,
    load_active_database_snapshot,
)
from app.infrastructure.kma_client import kma_client
from app.infrastructure.mock_store import mock_store
from app.utils.weather import get_closest_kma_base_time

KST = ZoneInfo("Asia/Seoul")
PROGRESS_LOG_INTERVAL = 10


def _log(message: str) -> None:
    timestamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp} KST] {message}", flush=True)


def _elapsed_seconds(started_at: float) -> float:
    return time.monotonic() - started_at


def _describe_error(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return f"HTTP {exc.status_code}: {exc.detail}"
    return str(exc) or type(exc).__name__


def _is_retryable(exc: Exception) -> bool:
    if not isinstance(exc, HTTPException):
        return True
    return exc.status_code in {
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        status.HTTP_502_BAD_GATEWAY,
        status.HTTP_503_SERVICE_UNAVAILABLE,
        status.HTTP_504_GATEWAY_TIMEOUT,
    }


def _is_no_data(exc: Exception) -> bool:
    return (
        isinstance(exc, HTTPException) and exc.status_code == status.HTTP_404_NOT_FOUND
    )


def _read_existing_snapshot(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "course_metadata": {},
            "village_forecasts": {},
            "climate_indices": {},
        }


def _write_json_snapshot(path: Path, snapshot: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)
    return path


async def _with_retry(operation_name: str, operation):
    last_error: Exception | None = None
    for attempt in range(1, settings.kma_collection_retries + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if not _is_retryable(exc):
                raise
            if attempt >= settings.kma_collection_retries:
                break
            retry_delay = settings.kma_collection_retry_seconds * (2 ** (attempt - 1))
            _log(
                f"재시도 대기: {operation_name} "
                f"({attempt}/{settings.kma_collection_retries}, "
                f"원인={_describe_error(exc)}, "
                f"{retry_delay}초 후 재시도)"
            )
            await asyncio.sleep(retry_delay)
    raise RuntimeError(
        f"{operation_name} failed after "
        f"{settings.kma_collection_retries} attempts: "
        f"{_describe_error(last_error)}"
    ) from last_error


async def collect_snapshot() -> str:
    if not settings.kma_service_key:
        raise RuntimeError("KMA_SERVICE_KEY is not configured")

    started_at = time.monotonic()
    base_time = get_closest_kma_base_time(publication_delay_minutes=10)
    snapshot_path = Path(settings.kma_snapshot_path)
    if settings.weather_storage == "database":
        await initialize_database()
        existing = await load_active_database_snapshot()
    else:
        existing = _read_existing_snapshot(snapshot_path)
    course_metadata = dict(existing.get("course_metadata", {}))
    village_forecasts = dict(existing.get("village_forecasts", {}))
    climate_indices = dict(existing.get("climate_indices", {}))

    courses = sorted(
        mock_store.courses.values(),
        key=lambda course: course.kma_course_id,
    )
    if settings.kma_course_limit > 0:
        courses = courses[: settings.kma_course_limit]
    semaphore = asyncio.Semaphore(settings.kma_collection_concurrency)
    total_courses = len(courses)
    completed_courses = 0
    successful_courses = 0
    no_data_courses = 0
    failed_courses = 0
    collected_forecast_rows = 0

    _log(
        "KMA 스냅샷 수집 시작: "
        f"기준시각={base_time}, 코스={total_courses}개, "
        f"동시요청={settings.kma_collection_concurrency}"
    )

    async def collect_course(course):
        nonlocal completed_courses
        nonlocal successful_courses
        nonlocal no_data_courses
        nonlocal failed_courses
        nonlocal collected_forecast_rows

        async with semaphore:
            try:
                result = await _with_retry(
                    f"동네예보 코스 {course.kma_course_id}",
                    lambda: kma_client.get_village_forecast(
                        course.kma_course_id,
                        base_time,
                    ),
                )
                successful_courses += 1
                collected_forecast_rows += len(result)
                return result
            except Exception as exc:
                if _is_no_data(exc):
                    no_data_courses += 1
                else:
                    failed_courses += 1
                raise
            finally:
                completed_courses += 1
                if (
                    completed_courses % PROGRESS_LOG_INTERVAL == 0
                    or completed_courses == total_courses
                ):
                    _log(
                        "동네예보 진행: "
                        f"{completed_courses}/{total_courses} "
                        f"({completed_courses / total_courses:.0%}), "
                        f"성공={successful_courses}, "
                        f"데이터없음={no_data_courses}, "
                        f"통신실패={failed_courses}, "
                        f"예보={collected_forecast_rows}건, "
                        f"경과={_elapsed_seconds(started_at):.1f}초"
                    )

    forecast_results = await asyncio.gather(
        *[collect_course(course) for course in courses],
        return_exceptions=True,
    )
    no_data_course_ids: list[int] = []
    failed_course_ids: list[int] = []
    for course, result in zip(courses, forecast_results, strict=True):
        if isinstance(result, Exception):
            target_ids = (
                no_data_course_ids if _is_no_data(result) else failed_course_ids
            )
            target_ids.append(course.kma_course_id)
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

    if no_data_course_ids:
        _log(
            "동네예보 데이터 없음(재시도 생략, 기존 데이터 유지): "
            f"{len(no_data_course_ids)}개 코스"
        )
    if failed_course_ids:
        _log(
            "경고: 재시도 후에도 동네예보를 가져오지 못한 코스 "
            f"{len(failed_course_ids)}개: " + ",".join(map(str, failed_course_ids))
        )

    city_area_ids = sorted(
        {
            course.city_area_id
            for course in mock_store.courses.values()
            if course.city_area_id
        }
    )
    _log(f"관광기후지수 수집 시작: 지역={len(city_area_ids)}개")

    async def collect_climate_index(city_area_id: str):
        async with semaphore:
            return await _with_retry(
                f"관광기후지수 지역 {city_area_id}",
                lambda: kma_client.get_climate_index(
                    city_area_id,
                    base_time,
                ),
            )

    climate_results = await asyncio.gather(
        *[collect_climate_index(city_area_id) for city_area_id in city_area_ids],
        return_exceptions=True,
    )
    for city_area_id, result in zip(
        city_area_ids,
        climate_results,
        strict=True,
    ):
        if isinstance(result, Exception):
            # Climate index publication can differ from village forecasts.
            _log(f"경고: 관광기후지수 지역 {city_area_id} 수집 실패: {result}")
            continue
        climate_indices[city_area_id] = result

    if not village_forecasts:
        raise RuntimeError("No village forecast data was collected")

    _log(
        "스냅샷 파일 저장 시작: "
        f"동네예보 코스={len(village_forecasts)}개, "
        f"관광기후지수 지역={len(climate_indices)}개"
    )
    snapshot = {
        "base_time": base_time,
        "collected_at": datetime.now(KST).isoformat(),
        "course_metadata": course_metadata,
        "village_forecasts": village_forecasts,
        "climate_indices": climate_indices,
    }
    if settings.weather_storage == "database":
        _log(f"MariaDB 스냅샷 저장 시작: 배치={settings.weather_database_batch_size}건")
        snapshot_id = await MariaDbWeatherSnapshotWriter(
            progress_callback=lambda label, completed, total: _log(
                f"MariaDB {label} 저장: {completed}/{total}건"
            )
        ).save(snapshot)
        destination = f"database snapshot_id={snapshot_id}"
    else:
        destination = str(_write_json_snapshot(snapshot_path, snapshot))

    _log(
        f"KMA 스냅샷 수집 완료: 저장소={destination}, "
        f"경과={_elapsed_seconds(started_at):.1f}초"
    )
    return destination


def main() -> None:
    destination = asyncio.run(collect_snapshot())
    _log(f"KMA snapshot updated: {destination}")


if __name__ == "__main__":
    main()
