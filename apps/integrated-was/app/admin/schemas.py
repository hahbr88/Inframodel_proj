from datetime import datetime

from pydantic import BaseModel

from app.queries.schemas import CourseCatalogItem


class AdminSessionResponse(BaseModel):
    status: str = "success"
    authenticated: bool = True
    role: str = "ADMIN"


class AdminDashboardResponse(BaseModel):
    status: str = "success"
    course_count: int
    reservation_count: int
    active_reservation_count: int
    cancelled_reservation_count: int
    upcoming_reservation_count: int


class AdminReservationResponse(BaseModel):
    id: int
    user_id: int
    username: str
    course_id: int
    course_name: str
    reservation_date: datetime
    status: str


class AdminReservationListResponse(BaseModel):
    status: str = "success"
    count: int
    reservations: list[AdminReservationResponse]


class AdminCourseListResponse(BaseModel):
    status: str = "success"
    forecast_time: str
    count: int
    total_count: int
    next_cursor: int | None = None
    has_next: bool
    courses: list[CourseCatalogItem]


class AdminUserResponse(BaseModel):
    id: int
    username: str
    role: str
    status: str
    reservation_count: int
    active_reservation_count: int


class AdminUserListResponse(BaseModel):
    status: str = "success"
    count: int
    users: list[AdminUserResponse]
