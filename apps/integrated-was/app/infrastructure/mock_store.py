import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.course_catalog import CatalogCourse, load_course_catalog

MOCK_DATA_PATH = Path(__file__).parent.parent / "data" / "mock_data.json"


@dataclass
class MockUser:
    id: int
    username: str
    password_hash: str
    status: str = "ACTIVE"


@dataclass
class MockReservation:
    id: int
    user_id: int
    course_id: int
    reservation_date: datetime
    status: str
    user: MockUser
    course: CatalogCourse


class MockStore:
    def __init__(self) -> None:
        self._snapshot_modified_at_ns: int | None = None
        self.reload()

    def reload(self) -> None:
        payload = json.loads(MOCK_DATA_PATH.read_text(encoding="utf-8"))
        self.metadata: dict[str, Any] = payload["metadata"]
        self.users = {
            item["username"]: MockUser(
                id=item["id"],
                username=item["username"],
                password_hash=hash_password(item["password"]),
            )
            for item in payload["users"]
        }
        # Mock mode must remain usable without a database or fixture-managed user.
        self.users[settings.demo_username] = MockUser(
            id=1,
            username=settings.demo_username,
            password_hash=hash_password(settings.demo_password),
        )
        self.users[settings.admin_username] = MockUser(
            id=1,
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
        )
        self.courses = load_course_catalog()
        for item in payload["courses"]:
            course_id = item["kma_course_id"]
            course = self.courses[course_id]
            course.name = item["name"]
            course.location = item["location"]
        self.reservations = {
            item["id"]: MockReservation(
                id=item["id"],
                user_id=item.get("user_id", 1),
                course_id=item["course_id"],
                reservation_date=datetime.fromisoformat(item["reservation_date"]),
                status=item["status"],
                user=self._find_user_by_id(item.get("user_id", 1)),
                course=self.courses[item["course_id"]],
            )
            for item in payload["reservations"]
        }
        self.village_forecasts: dict[str, Any] = payload["village_forecasts"]
        self.climate_indices: dict[str, Any] = payload["climate_indices"]
        self.pending_snapshot: dict[int, tuple[str, datetime]] | None = None
        self.refresh_course_metadata()

    def refresh_course_metadata(self) -> None:
        snapshot_path = Path(settings.kma_snapshot_path)
        try:
            modified_at_ns = snapshot_path.stat().st_mtime_ns
            if self._snapshot_modified_at_ns == modified_at_ns:
                return
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            metadata = snapshot.get("course_metadata", {})
            for key, item in metadata.items():
                course = self.courses.get(int(key))
                if course is None:
                    continue
                course.name = item.get("name") or course.name
                course.location = item.get("location") or course.location
            self._snapshot_modified_at_ns = modified_at_ns
        except (OSError, ValueError):
            return

    def next_reservation_id(self) -> int:
        return max(self.reservations, default=0) + 1

    def next_user_id(self) -> int:
        return max((user.id for user in self.users.values()), default=0) + 1

    def _find_user_by_id(self, user_id: int) -> MockUser:
        for user in self.users.values():
            if user.id == user_id:
                return user
        return self.users[settings.admin_username]


class MockCommandRepository:
    def __init__(self, store: MockStore):
        self.store = store

    async def get_user_by_username(self, username: str) -> MockUser | None:
        user = self.store.users.get(username)
        if user is None or user.status != "ACTIVE":
            return None
        return user

    async def get_user(self, user_id: int) -> MockUser | None:
        for user in self.store.users.values():
            if user.id == user_id and user.status == "ACTIVE":
                return user
        return None

    async def create_user(self, username: str, password_hash: str) -> MockUser:
        user = MockUser(
            id=self.store.next_user_id(),
            username=username,
            password_hash=password_hash,
        )
        self.store.users[user.username] = user
        return user

    async def update_user_password(
        self,
        user_id: int,
        password_hash: str,
    ) -> MockUser | None:
        user = await self.get_user(user_id)
        if user is not None:
            user.password_hash = password_hash
        return user

    async def deactivate_user(self, user_id: int) -> MockUser | None:
        user = await self.get_user(user_id)
        if user is not None:
            self.store.users.pop(user.username, None)
            user.status = "DELETED"
            user.username = f"deleted:{user.id}:{user.username}"
            self.store.users[user.username] = user
        return user

    async def get_course(self, course_id: int) -> CatalogCourse | None:
        self.store.refresh_course_metadata()
        return self.store.courses.get(course_id)

    async def create_reservation(
        self,
        user_id: int,
        course_id: int,
        reservation_date: datetime,
    ) -> MockReservation:
        reservation = MockReservation(
            id=self.store.next_reservation_id(),
            user_id=user_id,
            course_id=course_id,
            reservation_date=reservation_date,
            status="CONFIRMED",
            user=self.store._find_user_by_id(user_id),
            course=self.store.courses[course_id],
        )
        self.store.reservations[reservation.id] = reservation
        return reservation

    async def cancel_reservation(
        self,
        reservation_id: int,
        user_id: int | None = None,
    ) -> MockReservation | None:
        reservation = self._get_reservation(reservation_id, user_id)
        if reservation is not None:
            self.store.pending_snapshot = {
                reservation.id: (
                    reservation.status,
                    reservation.reservation_date,
                ),
            }
            reservation.status = "CANCELLED"
        return reservation

    async def update_reservation_date(
        self,
        reservation_id: int,
        reservation_date: datetime,
        user_id: int | None = None,
    ) -> MockReservation | None:
        reservation = self._get_reservation(reservation_id, user_id)
        if reservation is not None:
            self.store.pending_snapshot = {
                reservation.id: (
                    reservation.status,
                    reservation.reservation_date,
                ),
            }
            reservation.reservation_date = reservation_date
        return reservation

    def _get_reservation(
        self,
        reservation_id: int,
        user_id: int | None = None,
    ) -> MockReservation | None:
        reservation = self.store.reservations.get(reservation_id)
        if reservation is None:
            return None
        if user_id is not None and reservation.user_id != user_id:
            return None
        return reservation

    async def commit(self) -> None:
        self.store.pending_snapshot = None

    async def rollback(self) -> None:
        if self.store.pending_snapshot:
            for reservation_id, previous in self.store.pending_snapshot.items():
                old_status, old_date = previous
                reservation = self.store.reservations[reservation_id]
                reservation.status = old_status
                reservation.reservation_date = old_date
        self.store.pending_snapshot = None


class MockQueryRepository:
    def __init__(self, store: MockStore):
        self.store = store

    async def list_users(self) -> list[MockUser]:
        return sorted(self.store.users.values(), key=lambda item: item.id)

    async def list_courses(self) -> list[CatalogCourse]:
        self.store.refresh_course_metadata()
        return sorted(self.store.courses.values(), key=lambda item: item.id)

    async def get_course(self, course_id: int) -> CatalogCourse | None:
        self.store.refresh_course_metadata()
        return self.store.courses.get(course_id)

    async def list_reservations(
        self,
        user_id: int | None = None,
    ) -> list[MockReservation]:
        reservations = self.store.reservations.values()
        if user_id is not None:
            reservations = [
                reservation
                for reservation in reservations
                if reservation.user_id == user_id
            ]
        return sorted(
            reservations,
            key=lambda item: item.id,
            reverse=True,
        )


class MockWeatherClient:
    def __init__(self, store: MockStore):
        self.store = store

    @staticmethod
    async def resolve_base_time(suggested_base_time: str) -> str:
        return suggested_base_time

    async def get_village_forecast(
        self,
        course_id: int,
        base_time: str,
    ) -> list[dict[str, Any]]:
        sample = self._find_weather_by_kma_course_id(course_id)
        if sample is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mock forecast is not available for course {course_id}",
            )
        return sample

    async def get_climate_index(
        self,
        city_area_id: str,
        base_time: str,
    ) -> dict[str, float | str]:
        return self.store.climate_indices.get(
            city_area_id,
            next(iter(self.store.climate_indices.values())),
        )

    def _find_weather_by_kma_course_id(
        self,
        course_id: int,
    ) -> list[dict[str, Any]] | None:
        return self.store.village_forecasts.get(str(course_id))


mock_store = MockStore()
mock_command_repository = MockCommandRepository(mock_store)
mock_query_repository = MockQueryRepository(mock_store)
mock_weather_client = MockWeatherClient(mock_store)
