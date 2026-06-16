import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.jobs import collect_kma


@pytest.mark.asyncio
async def test_retry_skips_not_found(monkeypatch) -> None:
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise HTTPException(status_code=404, detail="no data")

    monkeypatch.setattr(settings, "kma_collection_retries", 3)

    with pytest.raises(HTTPException) as exc_info:
        await collect_kma._with_retry("test", operation)

    assert exc_info.value.status_code == 404
    assert calls == 1


@pytest.mark.asyncio
async def test_retry_uses_exponential_backoff(monkeypatch) -> None:
    calls = 0
    delays: list[int] = []

    async def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise HTTPException(status_code=504, detail="timeout")
        return "success"

    async def fake_sleep(delay: int) -> None:
        delays.append(delay)

    monkeypatch.setattr(settings, "kma_collection_retries", 3)
    monkeypatch.setattr(settings, "kma_collection_retry_seconds", 5)
    monkeypatch.setattr(collect_kma.asyncio, "sleep", fake_sleep)

    result = await collect_kma._with_retry("test", operation)

    assert result == "success"
    assert calls == 3
    assert delays == [5, 10]
