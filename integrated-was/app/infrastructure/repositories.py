from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Course, Reservation, User
from app.infrastructure.course_catalog import load_course_catalog


class CommandRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_course(self, course_id: int) -> Course | None:
        return await self.session.get(Course, course_id)

    async def create_reservation(
        self,
        course_id: int,
        reservation_date: datetime,
    ) -> Reservation:
        reservation = Reservation(
            course_id=course_id,
            reservation_date=reservation_date,
            status="CONFIRMED",
        )
        self.session.add(reservation)
        await self.session.flush()
        await self.session.refresh(reservation)
        return reservation

    async def update_reservation_date(
        self,
        reservation_id: int,
        reservation_date: datetime,
    ) -> Reservation | None:
        reservation = await self.session.get(Reservation, reservation_id)
        if reservation is not None:
            reservation.reservation_date = reservation_date
            await self.session.flush()
        return reservation

    async def cancel_reservation(self, reservation_id: int) -> Reservation | None:
        reservation = await self.session.get(Reservation, reservation_id)
        if reservation is not None:
            reservation.status = "CANCELLED"
            await self.session.flush()
        return reservation

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class QueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.course_catalog = load_course_catalog()

    async def list_courses(self) -> list[Course]:
        result = await self.session.execute(select(Course).order_by(Course.id))
        return [
            self._enrich_course(course)
            for course in result.scalars().all()
        ]

    async def get_course(self, course_id: int) -> Course | None:
        course = await self.session.get(Course, course_id)
        return None if course is None else self._enrich_course(course)

    async def list_reservations(self) -> list[Reservation]:
        result = await self.session.execute(
            select(Reservation)
            .options(selectinload(Reservation.course))
            .order_by(Reservation.id.desc())
        )
        return list(result.scalars().all())

    def _enrich_course(self, course: Course) -> Course:
        metadata = self.course_catalog.get(course.kma_course_id)
        course.spots = [] if metadata is None else metadata.spots
        course.spot_count = len(course.spots)
        course.themes = (
            []
            if metadata is None
            else metadata.themes
        )
        return course
