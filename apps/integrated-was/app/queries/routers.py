from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    get_query_repository,
    get_weather_client,
)
from app.core.security import require_authenticated_user
from app.infrastructure.ports import QueryRepositoryPort, WeatherClientPort
from app.queries.schemas import (
    ClimateIndexResponse,
    CourseDetailResponse,
    CourseCatalogResponse,
    CourseListResponse,
    ReservationListResponse,
    VillageForecastResponse,
    WeatherResponse,
)
from app.queries.services import (
    CourseQueryService,
    ReservationQueryService,
    WeatherQueryService,
)

router = APIRouter()


def get_course_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
) -> CourseQueryService:
    return CourseQueryService(repository)


def get_course_catalog_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
    weather_client: WeatherClientPort = Depends(get_weather_client),
) -> CourseQueryService:
    return CourseQueryService(repository, weather_client)


def get_reservation_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
) -> ReservationQueryService:
    return ReservationQueryService(repository)


def get_weather_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
    weather_client: WeatherClientPort = Depends(get_weather_client),
) -> WeatherQueryService:
    return WeatherQueryService(repository, weather_client)


@router.get("/courses", response_model=CourseListResponse, tags=["Query"])
async def list_courses(
    service: CourseQueryService = Depends(get_course_service),
) -> CourseListResponse:
    return await service.list_all()


@router.get(
    "/course-catalog",
    response_model=CourseCatalogResponse,
    tags=["Query"],
)
async def get_course_catalog(
    cursor: int | None = Query(
        default=None,
        ge=0,
        description="이전 응답의 next_cursor 값입니다.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 번에 반환할 코스 수입니다.",
    ),
    keyword: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="코스명, 지역, 테마, 관광지명 검색어입니다.",
    ),
    location: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="지역명 정확 일치 필터입니다.",
    ),
    theme: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="테마명 정확 일치 필터입니다.",
    ),
    include_spots: bool = Query(
        default=False,
        description="true이면 코스에 포함된 관광지 목록을 반환합니다.",
    ),
    include_forecasts: bool = Query(
        default=False,
        description="true이면 각 코스의 전체 시간대별 예보를 반환합니다.",
    ),
    service: CourseQueryService = Depends(get_course_catalog_service),
) -> CourseCatalogResponse:
    return await service.get_catalog(
        cursor=cursor,
        limit=limit,
        keyword=keyword,
        location=location,
        theme=theme,
        include_spots=include_spots,
        include_forecasts=include_forecasts,
    )


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetailResponse,
    tags=["Query"],
)
async def get_course_detail(
    course_id: int,
    service: CourseQueryService = Depends(get_course_catalog_service),
) -> CourseDetailResponse:
    return await service.get_detail(course_id)


@router.get(
    "/reservations",
    response_model=ReservationListResponse,
    tags=["Query"],
)
async def list_reservations(
    _user_id: int = Depends(require_authenticated_user),
    service: ReservationQueryService = Depends(get_reservation_service),
) -> ReservationListResponse:
    return await service.list_all()


@router.get(
    "/courses/{course_id}/village-forecast",
    response_model=VillageForecastResponse,
    tags=["Query", "KMA"],
)
async def get_village_forecast(
    course_id: int,
    service: WeatherQueryService = Depends(get_weather_service),
) -> VillageForecastResponse:
    return await service.get_village_forecast(course_id)


@router.get(
    "/courses/{course_id}/climate-index",
    response_model=ClimateIndexResponse,
    tags=["Query", "KMA"],
)
async def get_climate_index(
    course_id: int,
    service: WeatherQueryService = Depends(get_weather_service),
) -> ClimateIndexResponse:
    return await service.get_climate_index(course_id)


@router.get(
    "/courses/{course_id}/weather",
    response_model=WeatherResponse,
    tags=["Query", "KMA"],
)
async def get_course_weather(
    course_id: int,
    service: WeatherQueryService = Depends(get_weather_service),
) -> WeatherResponse:
    return await service.get_course_weather(course_id)
