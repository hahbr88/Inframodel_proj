from datetime import datetime
from typing import Any, Protocol


class CommandRepositoryPort(Protocol):
    async def get_user_by_username(self, username: str) -> Any | None: ...

    async def get_course(self, course_id: int) -> Any | None: ...

    async def create_reservation(
        self,
        course_id: int,
        reservation_date: datetime,
    ) -> Any: ...

    async def cancel_reservation(self, reservation_id: int) -> Any | None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class QueryRepositoryPort(Protocol):
    async def list_courses(self) -> list[Any]: ...

    async def get_course(self, course_id: int) -> Any | None: ...

    async def list_reservations(self) -> list[Any]: ...


class WeatherClientPort(Protocol):
    def resolve_base_time(self, suggested_base_time: str) -> str: ...

    async def get_village_forecast(
        self,
        course_id: int,
        base_time: str,
    ) -> list[dict[str, Any]]: ...

    async def get_climate_index(
        self,
        city_area_id: str,
        base_time: str,
    ) -> dict[str, float | str]: ...
