from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import hash_password
from app.domain.models import Base, Course, User
from app.infrastructure.course_catalog import load_course_catalog

write_engine = create_async_engine(
    settings.write_database_url,
    pool_pre_ping=True,
)
read_engine = create_async_engine(
    settings.read_database_url,
    pool_pre_ping=True,
)

WriteSessionFactory = async_sessionmaker(
    write_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
ReadSessionFactory = async_sessionmaker(
    read_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_write_session() -> AsyncIterator[AsyncSession]:
    async with WriteSessionFactory() as session:
        yield session


async def get_read_session() -> AsyncIterator[AsyncSession]:
    async with ReadSessionFactory() as session:
        yield session


async def initialize_database() -> None:
    # Schema migration should be handled by Alembic in production.
    async with write_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with WriteSessionFactory() as session:
        if not await session.scalar(select(User.id).limit(1)):
            session.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                )
            )

        existing_courses = {
            course.id: course
            for course in (await session.scalars(select(Course))).all()
        }
        catalog = load_course_catalog()
        known_overrides = {
            1: ("남호고택에서의 하룻밤", "경상북도"),
            52: ("자유여행코스 - 홍대", "서울특별시"),
        }
        for course_id, catalog_course in catalog.items():
            existing_course = existing_courses.get(course_id)
            if existing_course is not None:
                existing_course.city_area_id = catalog_course.city_area_id
                continue
            name, location = known_overrides.get(
                course_id,
                (
                    catalog_course.name,
                    catalog_course.location,
                ),
            )
            session.add(
                Course(
                    id=course_id,
                    name=name,
                    location=location,
                    kma_course_id=course_id,
                    city_area_id=catalog_course.city_area_id,
                )
            )
        await session.commit()
