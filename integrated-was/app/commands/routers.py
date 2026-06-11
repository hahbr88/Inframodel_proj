from fastapi import APIRouter, Depends, Response, status

from app.commands.schemas import (
    CommandResponse,
    LoginRequest,
    ReservationCreate,
    ReservationCreatedResponse,
    ReservationUpdate,
)
from app.commands.services import AuthCommandService, ReservationCommandService
from app.core.config import settings
from app.core.dependencies import get_command_repository
from app.core.security import require_authenticated_user
from app.infrastructure.ports import CommandRepositoryPort

router = APIRouter()


def get_auth_service(
    repository: CommandRepositoryPort = Depends(get_command_repository),
) -> AuthCommandService:
    return AuthCommandService(repository)


def get_reservation_service(
    repository: CommandRepositoryPort = Depends(get_command_repository),
) -> ReservationCommandService:
    return ReservationCommandService(repository)


@router.post("/auth/login", response_model=CommandResponse, tags=["Command"])
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthCommandService = Depends(get_auth_service),
) -> CommandResponse:
    token = await service.login(payload)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return CommandResponse(message="Login succeeded")


@router.post("/auth/logout", response_model=CommandResponse, tags=["Command"])
async def logout(response: Response) -> CommandResponse:
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return CommandResponse(message="Logout succeeded")


@router.post(
    "/reservations",
    response_model=ReservationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Command"],
)
async def create_reservation(
    payload: ReservationCreate,
    _user_id: int = Depends(require_authenticated_user),
    service: ReservationCommandService = Depends(get_reservation_service),
) -> ReservationCreatedResponse:
    reservation_id = await service.create(payload)
    return ReservationCreatedResponse(
        message="Reservation was created",
        reservation_id=reservation_id,
    )


@router.patch(
    "/reservations/{reservation_id}",
    response_model=CommandResponse,
    tags=["Command"],
)
async def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    _user_id: int = Depends(require_authenticated_user),
    service: ReservationCommandService = Depends(get_reservation_service),
) -> CommandResponse:
    await service.update(reservation_id, payload)
    return CommandResponse(message="Reservation was updated")


@router.delete(
    "/reservations/{reservation_id}",
    response_model=CommandResponse,
    tags=["Command"],
)
async def cancel_reservation(
    reservation_id: int,
    _user_id: int = Depends(require_authenticated_user),
    service: ReservationCommandService = Depends(get_reservation_service),
) -> CommandResponse:
    await service.cancel(reservation_id)
    return CommandResponse(message="Reservation was cancelled")
