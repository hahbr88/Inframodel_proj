from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class ReservationCreate(BaseModel):
    course_id: int = Field(gt=0)
    reservation_date: datetime


class ReservationUpdate(BaseModel):
    reservation_date: datetime


class CommandResponse(BaseModel):
    status: str = "success"
    message: str


class ReservationCreatedResponse(CommandResponse):
    reservation_id: int
