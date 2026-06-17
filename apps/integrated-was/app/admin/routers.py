from fastapi import APIRouter, Depends, Query, Response

from app.admin.schemas import (
    AdminCourseListResponse,
    AdminDashboardResponse,
    AdminReservationListResponse,
    AdminSessionResponse,
    AdminUserListResponse,
)
from app.admin.services import (
    AdminAuthService,
    AdminQueryService,
    AdminUserCommandService,
)
from app.commands.schemas import CommandResponse, LoginRequest, ReservationUpdate
from app.commands.services import ReservationCommandService
from app.core.config import settings
from app.core.dependencies import (
    get_command_repository,
    get_query_repository,
    get_weather_client,
)
from app.core.security import require_admin_user
from app.infrastructure.ports import (
    CommandRepositoryPort,
    QueryRepositoryPort,
    WeatherClientPort,
)
from app.queries.services import CourseQueryService

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_auth_service(
    repository: CommandRepositoryPort = Depends(get_command_repository),
) -> AdminAuthService:
    return AdminAuthService(repository)


def get_admin_query_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
) -> AdminQueryService:
    return AdminQueryService(repository)


def get_admin_reservation_service(
    repository: CommandRepositoryPort = Depends(get_command_repository),
) -> ReservationCommandService:
    return ReservationCommandService(repository)


def get_admin_user_service(
    repository: CommandRepositoryPort = Depends(get_command_repository),
) -> AdminUserCommandService:
    return AdminUserCommandService(repository)


def get_admin_course_service(
    repository: QueryRepositoryPort = Depends(get_query_repository),
    weather_client: WeatherClientPort = Depends(get_weather_client),
) -> CourseQueryService:
    return CourseQueryService(repository, weather_client)


@router.post("/auth/login", response_model=CommandResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AdminAuthService = Depends(get_admin_auth_service),
) -> CommandResponse:
    token = await service.login(payload)
    response.set_cookie(
        key="admin_access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return CommandResponse(message="Administrator login succeeded")


@router.post("/auth/logout", response_model=CommandResponse)
async def logout(response: Response) -> CommandResponse:
    response.delete_cookie(
        key="admin_access_token",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return CommandResponse(message="Administrator logout succeeded")


@router.get("/session", response_model=AdminSessionResponse)
async def get_session(
    _admin_id: int = Depends(require_admin_user),
) -> AdminSessionResponse:
    return AdminSessionResponse()


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
    _admin_id: int = Depends(require_admin_user),
    service: AdminQueryService = Depends(get_admin_query_service),
) -> AdminDashboardResponse:
    return await service.get_dashboard()


@router.get("/reservations", response_model=AdminReservationListResponse)
async def list_reservations(
    _admin_id: int = Depends(require_admin_user),
    service: AdminQueryService = Depends(get_admin_query_service),
) -> AdminReservationListResponse:
    return await service.list_reservations()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _admin_id: int = Depends(require_admin_user),
    service: AdminQueryService = Depends(get_admin_query_service),
) -> AdminUserListResponse:
    return await service.list_users()


@router.delete("/users/{user_id}", response_model=CommandResponse)
async def deactivate_user(
    user_id: int,
    _admin_id: int = Depends(require_admin_user),
    service: AdminUserCommandService = Depends(get_admin_user_service),
) -> CommandResponse:
    await service.deactivate(user_id)
    return CommandResponse(message="User was deactivated")


@router.patch("/reservations/{reservation_id}", response_model=CommandResponse)
async def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    _admin_id: int = Depends(require_admin_user),
    service: ReservationCommandService = Depends(get_admin_reservation_service),
) -> CommandResponse:
    await service.update(reservation_id, payload)
    return CommandResponse(message="Reservation was updated by administrator")


@router.delete("/reservations/{reservation_id}", response_model=CommandResponse)
async def cancel_reservation(
    reservation_id: int,
    _admin_id: int = Depends(require_admin_user),
    service: ReservationCommandService = Depends(get_admin_reservation_service),
) -> CommandResponse:
    await service.cancel(reservation_id)
    return CommandResponse(message="Reservation was cancelled by administrator")


@router.get("/courses", response_model=AdminCourseListResponse)
async def list_courses(
    cursor: int | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    _admin_id: int = Depends(require_admin_user),
    service: CourseQueryService = Depends(get_admin_course_service),
) -> AdminCourseListResponse:
    result = await service.get_catalog(
        cursor=cursor,
        limit=limit,
        keyword=keyword,
    )
    return AdminCourseListResponse(**result.model_dump())
