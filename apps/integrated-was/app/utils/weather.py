from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
KMA_BASE_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)


def get_closest_kma_base_time(
    current: datetime | None = None,
    publication_delay_minutes: int = 0,
) -> str:
    current = current or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    else:
        current = current.astimezone(KST)
    current -= timedelta(minutes=publication_delay_minutes)

    available_hours = [hour for hour in KMA_BASE_HOURS if hour <= current.hour]
    if available_hours:
        target = current.replace(
            hour=max(available_hours),
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        target = (current - timedelta(days=1)).replace(
            hour=23,
            minute=0,
            second=0,
            microsecond=0,
        )
    return target.strftime("%Y%m%d%H")
