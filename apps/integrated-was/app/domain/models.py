from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(30),
        default="USER",
        server_default="USER",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        server_default="ACTIVE",
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200))
    kma_course_id: Mapped[int] = mapped_column(index=True)
    city_area_id: Mapped[str] = mapped_column(String(20))


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    reservation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(lazy="joined")
    course: Mapped[Course] = relationship(lazy="joined")


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    base_time: Mapped[str] = mapped_column(String(10), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), index=True)
    forecast_count: Mapped[int] = mapped_column(default=0)
    climate_index_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("weather_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        primary_key=True,
        index=True,
    )
    spot_area_id: Mapped[int] = mapped_column(primary_key=True)
    forecast_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        index=True,
    )
    spot_area_name: Mapped[str] = mapped_column(String(100))
    spot_name: Mapped[str] = mapped_column(String(255))
    themes: Mapped[list[str]] = mapped_column(JSON, default=list)
    temperature: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    wind_direction: Mapped[int]
    wind_speed: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    sky: Mapped[int]
    humidity: Mapped[int]
    rain_probability: Mapped[int]


class ClimateIndex(Base):
    __tablename__ = "climate_indices"

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("weather_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    city_area_id: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        index=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    grade: Mapped[str] = mapped_column(String(30))
