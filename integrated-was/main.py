from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.commands.routers import router as command_router
from app.core.config import settings
from app.core.database import initialize_database
from app.queries.routers import router as query_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.data_mode == "database":
        await initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="CQRS-based weather, course, reservation, and authentication WAS",
    lifespan=lifespan,
)
app.include_router(command_router, prefix=settings.api_prefix)
app.include_router(query_router, prefix=settings.api_prefix)


@app.get("/", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "data_mode": settings.data_mode,
        "weather_mode": settings.weather_mode,
        "weather_storage": settings.weather_storage,
        "timezone": "Asia/Seoul",
    }
