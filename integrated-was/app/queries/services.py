import asyncio

from fastapi import HTTPException, status

from app.infrastructure.ports import QueryRepositoryPort, WeatherClientPort
from app.queries.schemas import (
    ClimateIndexResponse,
    CourseCatalogItem,
    CourseCatalogResponse,
    CourseListResponse,
    CourseResponse,
    CourseWeatherSummary,
    ReservationListResponse,
    ReservationResponse,
    TouristIndex,
    VillageForecastResponse,
    WeatherDetail,
    WeatherResponse,
)
from app.utils.weather import get_closest_kma_base_time


class CourseQueryService:
    def __init__(
        self,
        repository: QueryRepositoryPort,
        weather_client: WeatherClientPort | None = None,
    ):
        self.repository = repository
        self.weather_client = weather_client

    async def list_all(self) -> CourseListResponse:
        courses = await self.repository.list_courses()
        return CourseListResponse(
            count=len(courses),
            courses=[CourseResponse.model_validate(course) for course in courses],
        )

    async def get_catalog(
        self,
        include_forecasts: bool = True,
    ) -> CourseCatalogResponse:
        if self.weather_client is None:
            raise RuntimeError("Weather client is required for course catalog")

        courses, reservations = await asyncio.gather(
            self.repository.list_courses(),
            self.repository.list_reservations(),
        )
        active_counts: dict[int, int] = {}
        for reservation in reservations:
            if reservation.status != "CANCELLED":
                active_counts[reservation.course_id] = (
                    active_counts.get(reservation.course_id, 0) + 1
                )

        base_time = self.weather_client.resolve_base_time(
            get_closest_kma_base_time()
        )
        items = await asyncio.gather(
            *[
                self._build_catalog_item(
                    course,
                    base_time,
                    active_counts.get(course.id, 0),
                    include_forecasts,
                )
                for course in courses
            ]
        )
        return CourseCatalogResponse(
            forecast_time=base_time,
            count=len(items),
            courses=list(items),
        )

    async def _build_catalog_item(
        self,
        course,
        base_time: str,
        active_reservation_count: int,
        include_forecasts: bool,
    ) -> CourseCatalogItem:
        forecast_result, climate_result = await asyncio.gather(
            self.weather_client.get_village_forecast(
                course.kma_course_id,
                base_time,
            ),
            self.weather_client.get_climate_index(
                course.city_area_id,
                base_time,
            ),
            return_exceptions=True,
        )
        weather = (
            None
            if isinstance(forecast_result, Exception)
            else self._summarize_weather(forecast_result)
        )
        tourist_index = (
            None
            if isinstance(climate_result, Exception)
            else TouristIndex(**climate_result)
        )
        return CourseCatalogItem(
            id=course.id,
            name=course.name,
            location=course.location,
            kma_course_id=course.kma_course_id,
            spot_count=course.spot_count,
            themes=course.themes,
            spots=course.spots,
            weather=weather,
            forecasts=(
                [WeatherDetail(**item) for item in forecast_result]
                if include_forecasts
                and not isinstance(forecast_result, Exception)
                else []
            ),
            weather_available=weather is not None,
            tourist_index=tourist_index,
            active_reservation_count=active_reservation_count,
            reservation_enabled=True,
        )

    @staticmethod
    def _summarize_weather(
        forecasts: list[dict],
    ) -> CourseWeatherSummary | None:
        if not forecasts:
            return None
        forecast_at = min(item["forecast_at"] for item in forecasts)
        nearest = [
            item for item in forecasts if item["forecast_at"] == forecast_at
        ]
        themes = sorted(
            {
                theme
                for item in nearest
                for theme in item.get("themes", [])
            }
        )
        return CourseWeatherSummary(
            forecast_at=forecast_at,
            min_temperature=min(item["temperature"] for item in nearest),
            max_temperature=max(item["temperature"] for item in nearest),
            max_rain_probability=max(
                item["rain_probability"] for item in nearest
            ),
            average_humidity=round(
                sum(item["humidity"] for item in nearest) / len(nearest)
            ),
            worst_sky=max(item["sky"] for item in nearest),
            spot_count=len(nearest),
            themes=themes,
        )


class ReservationQueryService:
    def __init__(self, repository: QueryRepositoryPort):
        self.repository = repository

    async def list_all(self) -> ReservationListResponse:
        reservations = await self.repository.list_reservations()
        items = [
            ReservationResponse(
                id=reservation.id,
                course_id=reservation.course_id,
                course_name=reservation.course.name,
                reservation_date=reservation.reservation_date,
                status=reservation.status,
            )
            for reservation in reservations
        ]
        return ReservationListResponse(count=len(items), reservations=items)


class WeatherQueryService:
    def __init__(
        self,
        repository: QueryRepositoryPort,
        client: WeatherClientPort,
    ):
        self.repository = repository
        self.client = client

    async def get_village_forecast(
        self,
        course_id: int,
    ) -> VillageForecastResponse:
        course = await self.repository.get_course(course_id)
        if course is None:
            self._raise_course_not_found()

        base_time = self.client.resolve_base_time(
            get_closest_kma_base_time()
        )
        forecast_data = await self.client.get_village_forecast(
            course.kma_course_id,
            base_time,
        )
        forecasts = [WeatherDetail(**item) for item in forecast_data]
        return VillageForecastResponse(
            course_id=course.id,
            location=course.location,
            forecast_time=base_time,
            count=len(forecasts),
            forecasts=forecasts,
        )

    async def get_climate_index(
        self,
        course_id: int,
    ) -> ClimateIndexResponse:
        course = await self.repository.get_course(course_id)
        if course is None:
            self._raise_course_not_found()

        base_time = self.client.resolve_base_time(
            get_closest_kma_base_time()
        )
        climate_data = await self.client.get_climate_index(
            course.city_area_id,
            base_time,
        )
        return ClimateIndexResponse(
            course_id=course.id,
            location=course.location,
            forecast_time=base_time,
            tourist_index=TouristIndex(**climate_data),
        )

    async def get_course_weather(self, course_id: int) -> WeatherResponse:
        course = await self.repository.get_course(course_id)
        if course is None:
            self._raise_course_not_found()

        base_time = self.client.resolve_base_time(
            get_closest_kma_base_time()
        )
        forecast_data, climate_data = await asyncio.gather(
            self.client.get_village_forecast(course.kma_course_id, base_time),
            self.client.get_climate_index(course.city_area_id, base_time),
            return_exceptions=True,
        )
        if isinstance(forecast_data, Exception):
            raise forecast_data
        forecasts = [WeatherDetail(**item) for item in forecast_data]
        tourist_index = (
            None
            if isinstance(climate_data, Exception)
            else TouristIndex(**climate_data)
        )
        return WeatherResponse(
            course_id=course.id,
            location=course.location,
            forecast_time=base_time,
            forecast_count=len(forecasts),
            forecasts=forecasts,
            tourist_index=tourist_index,
        )

    @staticmethod
    def _raise_course_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course was not found",
        )
