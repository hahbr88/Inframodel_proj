from datetime import datetime

from fastapi import HTTPException, status

from app.commands.schemas import (
    LoginRequest,
    ReservationCreate,
    ReservationUpdate,
)
from app.core.security import create_access_token, verify_password
from app.infrastructure.ports import CommandRepositoryPort


class AuthCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository

    async def login(self, payload: LoginRequest) -> str:
        user = await self.repository.get_user_by_username(payload.username)
        if user is None or not verify_password(
            payload.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        return create_access_token(str(user.id), getattr(user, "role", "USER"))


class ReservationCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository

    async def create(self, payload: ReservationCreate) -> int:
        if await self.repository.get_course(payload.course_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course was not found",
            )
        self._validate_future_date(payload.reservation_date)
        try:
            reservation = await self.repository.create_reservation(
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
    ) -> None:
        self._validate_future_date(payload.reservation_date)
        try:
            reservation = await self.repository.update_reservation_date(
                reservation_id,
                payload.reservation_date,
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

    async def cancel(self, reservation_id: int) -> None:
        try:
            reservation = await self.repository.cancel_reservation(reservation_id)
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
