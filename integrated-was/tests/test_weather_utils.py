from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.weather import get_closest_kma_base_time

KST = ZoneInfo("Asia/Seoul")


def test_uses_previous_day_before_first_publication() -> None:
    current = datetime(2026, 6, 10, 1, 30, tzinfo=KST)

    assert get_closest_kma_base_time(current) == "2026060923"


def test_uses_latest_publication_hour() -> None:
    current = datetime(2026, 6, 10, 16, 30, tzinfo=KST)

    assert get_closest_kma_base_time(current) == "2026061014"


def test_publication_delay_uses_previous_base_time() -> None:
    current = datetime(2026, 6, 10, 2, 5, tzinfo=KST)

    assert (
        get_closest_kma_base_time(
            current,
            publication_delay_minutes=10,
        )
        == "2026060923"
    )
