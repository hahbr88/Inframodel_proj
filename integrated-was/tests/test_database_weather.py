from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.domain.models import (
    Base,
    ClimateIndex,
    Course,
    WeatherForecast,
    WeatherSnapshot,
)
from app.infrastructure import database_weather
from app.infrastructure.database_weather import (
    DatabaseWeatherClient,
    MariaDbWeatherSnapshotWriter,
    load_active_database_snapshot,
)


@pytest_asyncio.fixture
async def weather_database():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        session.add(
            Course(
                id=1,
                name="테스트 코스",
                location="경상북도",
                kma_course_id=1,
                city_area_id="4792000000",
            )
        )
        await session.commit()
    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_database_writer_activates_validated_snapshot(
    weather_database,
) -> None:
    writer = MariaDbWeatherSnapshotWriter(
        session_factory=weather_database,
        batch_size=2,
        retention=1,
    )

    first_id = await writer.save(_snapshot("2026061111", 20.0))
    second_id = await writer.save(_snapshot("2026061114", 24.0))

    async with weather_database() as session:
        snapshots = list(
            (
                await session.scalars(
                    select(WeatherSnapshot).order_by(WeatherSnapshot.id)
                )
            ).all()
        )
        forecast_count = await session.scalar(
            select(func.count()).select_from(WeatherForecast)
        )
        climate_count = await session.scalar(
            select(func.count()).select_from(ClimateIndex)
        )

    assert first_id != second_id
    assert [item.status for item in snapshots] == ["ARCHIVED", "ACTIVE"]
    assert snapshots[-1].forecast_count == 3
    assert snapshots[-1].climate_index_count == 1
    assert forecast_count == 6
    assert climate_count == 2


@pytest.mark.asyncio
async def test_database_client_reads_only_active_snapshot(
    weather_database,
    monkeypatch,
) -> None:
    writer = MariaDbWeatherSnapshotWriter(
        session_factory=weather_database,
        batch_size=2,
    )
    await writer.save(_snapshot("2026061111", 20.0))
    await writer.save(_snapshot("2026061114", 24.0))
    monkeypatch.setattr(
        database_weather,
        "ReadSessionFactory",
        weather_database,
    )
    client = DatabaseWeatherClient()

    base_time = await client.resolve_base_time("ignored")
    forecasts = await client.get_village_forecast(1, "ignored")
    climate = await client.get_climate_index("4792000000", "ignored")

    assert base_time == "2026061114"
    assert len(forecasts) == 3
    assert forecasts[0]["temperature"] == 24.0
    assert climate == {"score": 0.46, "grade": "매우좋음"}


@pytest.mark.asyncio
async def test_active_database_snapshot_can_seed_next_collection(
    weather_database,
    monkeypatch,
) -> None:
    writer = MariaDbWeatherSnapshotWriter(
        session_factory=weather_database,
        batch_size=2,
    )
    await writer.save(_snapshot("2026061114", 24.0))
    monkeypatch.setattr(
        database_weather,
        "WriteSessionFactory",
        weather_database,
    )

    snapshot = await load_active_database_snapshot()

    assert snapshot["base_time"] == "2026061114"
    assert len(snapshot["village_forecasts"]["1"]) == 3
    assert snapshot["climate_indices"]["4792000000"]["grade"] == "매우좋음"


def _snapshot(base_time: str, temperature: float) -> dict:
    return {
        "base_time": base_time,
        "collected_at": datetime.now().astimezone().isoformat(),
        "course_metadata": {},
        "village_forecasts": {
            "1": [
                {
                    "forecast_at": f"2026-06-11 {hour}:00",
                    "themes": ["자연/힐링"],
                    "spot_area_id": 101,
                    "spot_area_name": "봉화",
                    "spot_name": "테스트 지점",
                    "temperature": temperature + index,
                    "wind_direction": 270,
                    "wind_speed": 2.0,
                    "sky": 1,
                    "humidity": 50,
                    "rain_probability": 10,
                }
                for index, hour in enumerate(("15", "18", "21"))
            ]
        },
        "climate_indices": {
            "4792000000": {
                "score": 0.46,
                "grade": "매우좋음",
            }
        },
    }
