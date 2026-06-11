from app.infrastructure.kma_client import KmaClient


def test_duplicate_weather_rows_merge_themes() -> None:
    items = [
        {
            "tm": "2026-06-10 18:00",
            "thema": "문화/예술",
            "spotAreaId": 102,
            "spotAreaName": "봉화",
            "spotName": "테스트 지점",
            "th3": 25,
            "wd": 280,
            "ws": 2,
            "sky": 1,
            "rhm": 60,
            "pop": 20,
        },
        {
            "tm": "2026-06-10 18:00",
            "thema": "자연/힐링",
            "spotAreaId": 102,
            "spotAreaName": "봉화",
            "spotName": "테스트 지점",
            "th3": 25,
            "wd": 280,
            "ws": 2,
            "sky": 1,
            "rhm": 60,
            "pop": 20,
        },
    ]

    forecasts = KmaClient.normalize_village_forecasts(items)

    assert len(forecasts) == 1
    assert forecasts[0]["themes"] == ["문화/예술", "자연/힐링"]
