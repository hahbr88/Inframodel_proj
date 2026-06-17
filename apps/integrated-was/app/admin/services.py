from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.admin.schemas import (
    AdminDashboardResponse,
    AdminReservationListResponse,
    AdminReservationResponse,
    AdminUserListResponse,
    AdminUserResponse,
)
from app.commands.schemas import LoginRequest
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.infrastructure.accounts import get_account_provider
from app.infrastructure.ports import CommandRepositoryPort, QueryRepositoryPort


class AdminAuthService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository

    async def login(self, payload: LoginRequest) -> str:
        user = await self.repository.get_user_by_username(payload.username)
        if (
            user is None
            or not verify_password(payload.password, user.password_hash)
            or user.username != settings.admin_username
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid administrator credentials",
            )
        return create_access_token(str(user.id), "ADMIN")


class AdminQueryService:
    def __init__(self, repository: QueryRepositoryPort):
        self.repository = repository

    async def get_dashboard(self) -> AdminDashboardResponse:
        courses = await self.repository.list_courses()
        reservations = await self.repository.list_reservations()
        now = datetime.now(UTC)
        active = [
            reservation
            for reservation in reservations
            if reservation.status != "CANCELLED"
        ]
        upcoming = [
            reservation
            for reservation in active
            if self._as_aware(reservation.reservation_date) > now
        ]
        return AdminDashboardResponse(
            course_count=len(courses),
            reservation_count=len(reservations),
            active_reservation_count=len(active),
            cancelled_reservation_count=len(reservations) - len(active),
            upcoming_reservation_count=len(upcoming),
        )

    async def list_reservations(self) -> AdminReservationListResponse:
        reservations = await self.repository.list_reservations()
        items = [
            AdminReservationResponse(
                id=reservation.id,
                user_id=reservation.user_id,
                username=reservation.user.username,
                course_id=reservation.course_id,
                course_name=reservation.course.name,
                reservation_date=reservation.reservation_date,
                status=reservation.status,
            )
            for reservation in reservations
        ]
        return AdminReservationListResponse(count=len(items), reservations=items)

    async def list_users(self) -> AdminUserListResponse:
        users = await self.repository.list_users()
        reservations = await self.repository.list_reservations()
        items = [
            AdminUserResponse(
                id=user.id,
                username=user.username,
                status=getattr(user, "status", "ACTIVE"),
                reservation_count=sum(
                    1 for reservation in reservations if reservation.user_id == user.id
                ),
                active_reservation_count=sum(
                    1
                    for reservation in reservations
                    if reservation.user_id == user.id
                    and reservation.status != "CANCELLED"
                ),
            )
            for user in users
        ]
        return AdminUserListResponse(count=len(items), users=items)

    @staticmethod
    def _as_aware(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class AdminUserCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository
        self.account_provider = get_account_provider()

    async def deactivate(self, user_id: int) -> None:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User was not found",
            )
        if user.username == settings.admin_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Administrator account cannot be deactivated",
            )
        if settings.account_provider == "cognito":
            self.account_provider.delete_user(user.username)
        try:
            await self.repository.deactivate_user(user_id)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise
