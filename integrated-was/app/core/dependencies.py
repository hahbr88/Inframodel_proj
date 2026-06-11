from collections.abc import AsyncIterator

from app.core.config import settings
from app.core.database import ReadSessionFactory, WriteSessionFactory
from app.infrastructure.kma_client import kma_client
from app.infrastructure.mock_store import (
    mock_command_repository,
    mock_query_repository,
    mock_weather_client,
)
from app.infrastructure.ports import (
    CommandRepositoryPort,
    QueryRepositoryPort,
    WeatherClientPort,
)
from app.infrastructure.repositories import CommandRepository, QueryRepository
from app.infrastructure.snapshot_weather import snapshot_weather_client


async def get_command_repository() -> AsyncIterator[CommandRepositoryPort]:
    if settings.data_mode == "mock":
        yield mock_command_repository
        return

    async with WriteSessionFactory() as session:
        yield CommandRepository(session)


async def get_query_repository() -> AsyncIterator[QueryRepositoryPort]:
    if settings.data_mode == "mock":
        yield mock_query_repository
        return

    async with ReadSessionFactory() as session:
        yield QueryRepository(session)


def get_weather_client() -> WeatherClientPort:
    if settings.weather_mode == "mock":
        return mock_weather_client
    if settings.weather_mode == "snapshot":
        return snapshot_weather_client
    return kma_client
