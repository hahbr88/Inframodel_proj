from datetime import datetime

from fastapi import HTTPException, status

from app.commands.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    ReservationCreate,
    ReservationUpdate,
    SignupRequest,
)
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.infrastructure.accounts import get_account_provider
from app.infrastructure.ports import CommandRepositoryPort


class AuthCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository
        self.account_provider = get_account_provider()

    async def signup(self, payload: SignupRequest) -> str:
        if await self.repository.get_user_by_username(payload.username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already registered",
            )
        self.account_provider.create_user(payload.username, payload.password)
        try:
            user = await self.repository.create_user(
                payload.username,
                hash_password(payload.password),
            )
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            try:
                self.account_provider.delete_user(payload.username)
            except Exception:
                pass
            raise
        return create_access_token(str(user.id), "USER")

    async def login(self, payload: LoginRequest) -> str:
        user = await self.repository.get_user_by_username(payload.username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if getattr(settings, "account_provider", "local") == "cognito":
            self.account_provider.authenticate(payload.username, payload.password)
        elif not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        return create_access_token(str(user.id), getattr(user, "role", "USER"))

    async def change_password(
        self,
        user_id: int,
        payload: PasswordChangeRequest,
    ) -> None:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User was not found",
            )
        if settings.account_provider == "cognito":
            self.account_provider.change_password(
                user.username,
                payload.current_password,
                payload.new_password,
            )
        elif not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        try:
            await self.repository.update_user_password(
                user_id,
                hash_password(payload.new_password),
            )
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise

    async def delete_account(self, user_id: int, payload: LoginRequest) -> None:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User was not found",
            )
        if user.username != payload.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account confirmation does not match current user",
            )
        if settings.account_provider == "cognito":
            self.account_provider.authenticate(payload.username, payload.password)
            self.account_provider.delete_user(payload.username)
        elif not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        try:
            deleted = await self.repository.deactivate_user(user_id)
            if deleted is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User was not found",
                )
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise


class ReservationCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository

    async def create(self, user_id: int, payload: ReservationCreate) -> int:
        if await self.repository.get_course(payload.course_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course was not found",
            )
        self._validate_future_date(payload.reservation_date)
        try:
            reservation = await self.repository.create_reservation(
                user_id,
                payload.course_id,
                payload.reservation_date,
            )
            await self.repository.commit()
            return reservation.id
        except Exception:
            await self.repository.rollback()
            raise

    async def update(
        self,
        reservation_id: int,
        payload: ReservationUpdate,
        user_id: int | None = None,
    ) -> None:
        self._validate_future_date(payload.reservation_date)
        try:
            reservation = await self.repository.update_reservation_date(
                reservation_id,
                payload.reservation_date,
                user_id,
            )
            if reservation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reservation was not found",
                )
            if reservation.status == "CANCELLED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cancelled reservation cannot be updated",
                )
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise

    async def cancel(self, reservation_id: int, user_id: int | None = None) -> None:
        try:
            reservation = await self.repository.cancel_reservation(
                reservation_id,
                user_id,
            )
            if reservation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reservation was not found",
                )
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise

    @staticmethod
    def _validate_future_date(reservation_date: datetime) -> None:
        now = (
            datetime.now(reservation_date.tzinfo)
            if reservation_date.tzinfo
            else datetime.now()
        )
        if reservation_date <= now:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reservation date must be in the future",
            )
