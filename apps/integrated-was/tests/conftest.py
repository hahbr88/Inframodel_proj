import os
from pathlib import Path

TEST_DATABASE = Path(__file__).parent / "test.db"
os.environ["WRITE_DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{TEST_DATABASE.as_posix()}"
)
os.environ["READ_DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{TEST_DATABASE.as_posix()}"
)
os.environ["DATA_MODE"] = "mock"
os.environ["WEATHER_MODE"] = "mock"


def pytest_sessionfinish(session, exitstatus) -> None:
    TEST_DATABASE.unlink(missing_ok=True)
