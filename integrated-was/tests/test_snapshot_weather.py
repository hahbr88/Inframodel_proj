import json

import pytest
from fastapi import HTTPException

from app.infrastructure.snapshot_weather import SnapshotWeatherClient
from app.queries.services import WeatherQueryService


@pytest.mark.asyncio
async def test_snapshot_client_reads_collected_data(tmp_path) -> None:
    snapshot_path = tmp_path / "kma_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "base_time": "2026061014",
                "village_forecasts": {
                    "1": [
                        {
                            "forecast_at": "2026-06-10 18:00",
                            "themes": ["문화/예술"],
                            "spot_area_id": 102,
                            "spot_area_name": "봉화",
                            "spot_name": "테스트 지점",
                            "temperature": 25.0,
                            "wind_direction": 280,
                            "wind_speed": 2.0,
                            "sky": 1,
                            "humidity": 60,
                            "rain_probability": 20,
                        }
                    ]
                },
                "climate_indices": {
                    "35": {"score": 80.0, "grade": "좋음"}
                },
            }
        ),
        encoding="utf-8",
    )
    client = SnapshotWeatherClient(str(snapshot_path))

    forecast = await client.get_village_forecast(1, "ignored")
    climate = await client.get_climate_index("35", "ignored")

    assert await client.resolve_base_time("ignored") == "2026061014"
    assert forecast[0]["temperature"] == 25.0
    assert climate["score"] == 80.0


@pytest.mark.asyncio
async def test_snapshot_client_requires_initial_collection(tmp_path) -> None:
    client = SnapshotWeatherClient(str(tmp_path / "missing.json"))

    with pytest.raises(HTTPException) as exc_info:
        await client.get_village_forecast(1, "2026061014")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_integrated_weather_allows_missing_climate_index(
    tmp_path,
) -> None:
    snapshot_path = tmp_path / "kma_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "base_time": "2026061014",
                "village_forecasts": {
                    "1": [
                        {
                            "forecast_at": "2026-06-10 18:00",
                            "themes": ["문화/예술"],
                            "spot_area_id": 102,
                            "spot_area_name": "봉화",
                            "spot_name": "테스트 지점",
                            "temperature": 25.0,
                            "wind_direction": 280,
                            "wind_speed": 2.0,
                            "sky": 1,
                            "humidity": 60,
                            "rain_probability": 20,
                        }
                    ]
                },
                "climate_indices": {},
            }
        ),
        encoding="utf-8",
    )
    course = type(
        "Course",
        (),
        {
            "id": 1,
            "location": "경상북도",
            "kma_course_id": 1,
            "city_area_id": "35",
        },
    )()
    repository = type(
        "Repository",
        (),
        {"get_course": lambda self, course_id: _async_value(course)},
    )()
    service = WeatherQueryService(
        repository,
        SnapshotWeatherClient(str(snapshot_path)),
    )

    response = await service.get_course_weather(1)

    assert response.forecast_count == 1
    assert response.forecasts[0].temperature == 25.0
    assert response.tourist_index is None


async def _async_value(value):
    return value
