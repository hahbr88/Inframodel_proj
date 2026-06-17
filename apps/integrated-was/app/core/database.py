from collections.abc import AsyncIterator

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import hash_password, verify_password
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
        await _ensure_user_status_column(session)

        admin_user = await session.scalar(
            select(User).where(User.username == settings.admin_username)
        )
        if admin_user is None:
            admin_user = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
            )
            session.add(admin_user)
            await session.flush()
        elif not verify_password(
            settings.admin_password,
            admin_user.password_hash,
        ):
            admin_user.password_hash = hash_password(settings.admin_password)
            await session.flush()

        await _ensure_reservation_owner_column(session, admin_user.id)

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


async def _ensure_reservation_owner_column(
    session: AsyncSession,
    default_user_id: int,
) -> None:
    connection = await session.connection()

    def has_user_id(sync_connection) -> bool:
        inspector = inspect(sync_connection)
        if not inspector.has_table("reservations"):
            return True
        columns = inspector.get_columns("reservations")
        return any(column["name"] == "user_id" for column in columns)

    if await connection.run_sync(has_user_id):
        return

    await session.execute(text("ALTER TABLE reservations ADD COLUMN user_id INTEGER"))
    await session.execute(
        text("UPDATE reservations SET user_id = :user_id WHERE user_id IS NULL"),
        {"user_id": default_user_id},
    )
    await session.execute(
        text("CREATE INDEX ix_reservations_user_id ON reservations (user_id)")
    )


async def _ensure_user_status_column(session: AsyncSession) -> None:
    connection = await session.connection()

    def has_status(sync_connection) -> bool:
        inspector = inspect(sync_connection)
        if not inspector.has_table("users"):
            return True
        columns = inspector.get_columns("users")
        return any(column["name"] == "status" for column in columns)

    if await connection.run_sync(has_status):
        return

    await session.execute(
        text("ALTER TABLE users ADD COLUMN status VARCHAR(30) DEFAULT 'ACTIVE'")
    )
    await session.execute(
        text("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL")
    )
