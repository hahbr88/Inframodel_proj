from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


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
