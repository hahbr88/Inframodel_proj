from fastapi import HTTPException, status

from app.commands.schemas import LoginRequest, ReservationCreate
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
        return create_access_token(str(user.id))


class ReservationCommandService:
    def __init__(self, repository: CommandRepositoryPort):
        self.repository = repository

    async def create(self, payload: ReservationCreate) -> int:
        if await self.repository.get_course(payload.course_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course was not found",
            )
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

    async def cancel(self, reservation_id: int) -> None:
        try:
            reservation = await self.repository.cancel_reservation(
                reservation_id
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
