import pytest
from fastapi import status

from app.core.config import settings
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


def test_kma_result_code_mapping() -> None:
    assert KmaClient._map_result_code_to_status("03") == status.HTTP_404_NOT_FOUND
    assert (
        KmaClient._map_result_code_to_status("21") == status.HTTP_429_TOO_MANY_REQUESTS
    )
    assert KmaClient._map_result_code_to_status("30") == status.HTTP_400_BAD_REQUEST
    assert KmaClient._map_result_code_to_status("01") == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_kma_request_collects_all_pages(monkeypatch) -> None:
    client = KmaClient()
    requested_pages: list[int] = []

    async def fake_request_page(_client, _endpoint, request_params):
        page_no = request_params["pageNo"]
        requested_pages.append(page_no)
        start = (page_no - 1) * 300
        end = min(start + 300, 720)
        return {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL"},
                "body": {
                    "totalCount": 720,
                    "items": {"item": [{"row": index} for index in range(start, end)]},
                },
            }
        }

    monkeypatch.setattr(settings, "kma_service_key", "test-key")
    monkeypatch.setattr(client, "_request_page", fake_request_page)

    items = await client._request_items("test-endpoint", {})

    assert requested_pages == [1, 2, 3]
    assert len(items) == 720
    assert items[0]["row"] == 0
    assert items[-1]["row"] == 719


@pytest.mark.asyncio
async def test_climate_index_uses_date_without_hour(monkeypatch) -> None:
    client = KmaClient()
    captured_params = {}

    async def fake_request_items(_endpoint, params):
        captured_params.update(params)
        return [{"kmaTci": 0.46, "TCI_GRADE": "매우좋음"}]

    async def fake_cache_get(_key):
        return None

    async def fake_cache_set(_key, _value, ttl):
        assert ttl == 21600

    monkeypatch.setattr(client, "_request_items", fake_request_items)
    monkeypatch.setattr("app.infrastructure.kma_client.cache.get", fake_cache_get)
    monkeypatch.setattr("app.infrastructure.kma_client.cache.set", fake_cache_set)

    result = await client.get_climate_index(
        "4792000000",
        "2026061111",
    )

    assert captured_params["CURRENT_DATE"] == "20260611"
    assert captured_params["DAY"] == 0
    assert result == {"score": 0.46, "grade": "매우좋음"}
