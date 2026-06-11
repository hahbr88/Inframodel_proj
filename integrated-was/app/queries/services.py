import asyncio

from fastapi import HTTPException, status

from app.infrastructure.ports import QueryRepositoryPort, WeatherClientPort
from app.queries.schemas import (
    ClimateIndexResponse,
    CourseCatalogItem,
    CourseCatalogResponse,
    CourseDetailResponse,
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
        cursor: int | None = None,
        limit: int = 20,
        keyword: str | None = None,
        location: str | None = None,
        theme: str | None = None,
        include_spots: bool = False,
        include_forecasts: bool = False,
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

        filtered_courses = [
            course
            for course in courses
            if self._matches_filters(course, keyword, location, theme)
        ]
        total_count = len(filtered_courses)
        if cursor is not None:
            filtered_courses = [
                course for course in filtered_courses if course.id > cursor
            ]
        page_courses = filtered_courses[: limit + 1]
        has_next = len(page_courses) > limit
        page_courses = page_courses[:limit]

        base_time = await self.weather_client.resolve_base_time(
            get_closest_kma_base_time()
        )
        items = await asyncio.gather(
            *[
                self._build_catalog_item(
                    course,
                    base_time,
                    active_counts.get(course.id, 0),
                    include_spots,
                    include_forecasts,
                )
                for course in page_courses
            ]
        )
        return CourseCatalogResponse(
            forecast_time=base_time,
            count=len(items),
            total_count=total_count,
            next_cursor=items[-1].id if has_next and items else None,
            has_next=has_next,
            courses=list(items),
        )

    @staticmethod
    def _matches_filters(
        course,
        keyword: str | None,
        location: str | None,
        theme: str | None,
    ) -> bool:
        if location and course.location.casefold() != location.strip().casefold():
            return False
        if theme and not any(
            item.casefold() == theme.strip().casefold()
            for item in getattr(course, "themes", [])
        ):
            return False
        if keyword is None or not keyword.strip():
            return True

        normalized_keyword = keyword.strip().casefold()
        searchable_values = [
            course.name,
            course.location,
            *getattr(course, "themes", []),
            *[
                spot.name
                for spot in getattr(course, "spots", [])
            ],
        ]
        return any(
            normalized_keyword in str(value).casefold()
            for value in searchable_values
        )

    async def get_detail(self, course_id: int) -> CourseDetailResponse:
        if self.weather_client is None:
            raise RuntimeError("Weather client is required for course detail")

        course, reservations = await asyncio.gather(
            self.repository.get_course(course_id),
            self.repository.list_reservations(),
        )
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course was not found",
            )

        active_reservation_count = sum(
            1
            for reservation in reservations
            if reservation.course_id == course_id
            and reservation.status != "CANCELLED"
        )
        base_time = await self.weather_client.resolve_base_time(
            get_closest_kma_base_time()
        )
        item = await self._build_catalog_item(
            course,
            base_time,
            active_reservation_count,
            include_spots=True,
            include_forecasts=True,
        )
        return CourseDetailResponse(
            **item.model_dump(),
            forecast_time=base_time,
        )

    async def _build_catalog_item(
        self,
        course,
        base_time: str,
        active_reservation_count: int,
        include_spots: bool,
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
            spots=course.spots if include_spots else [],
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
            if reservation.status != "CANCELLED"
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

        base_time = await self.client.resolve_base_time(
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

        base_time = await self.client.resolve_base_time(
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

        base_time = await self.client.resolve_base_time(
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
