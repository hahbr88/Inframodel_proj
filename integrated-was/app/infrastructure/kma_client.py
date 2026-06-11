from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.infrastructure.cache import cache

KMA_MAX_ROWS_PER_REQUEST = 300


class KmaClient:
    @staticmethod
    def resolve_base_time(suggested_base_time: str) -> str:
        return suggested_base_time

    async def get_village_forecast(
        self,
        course_id: int,
        base_time: str,
    ) -> list[dict[str, Any]]:
        cache_key = f"kma:village:{course_id}:{base_time}"
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        items = await self._request_items(
            "getTourStnVilageFcst1",
            {
                "CURRENT_DATE": base_time,
                "HOUR": 24,
                "COURSE_ID": course_id,
            },
        )
        forecasts = self.normalize_village_forecasts(items)
        await cache.set(cache_key, forecasts, ttl=10800)
        return forecasts

    @staticmethod
    def normalize_village_forecasts(
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped_forecasts: dict[tuple[Any, ...], dict[str, Any]] = {}
        for item in items:
            forecast = {
                "course_name": item.get("courseName", ""),
                "course_area_name": item.get("courseAreaName", ""),
                "forecast_at": item.get("tm"),
                "themes": [],
                "spot_area_id": int(item.get("spotAreaId", 0)),
                "spot_area_name": item.get("spotAreaName", ""),
                "spot_name": item.get("spotName", ""),
                "temperature": float(item.get("th3", 0)),
                "wind_direction": int(item.get("wd", 0)),
                "wind_speed": float(item.get("ws", 0)),
                "sky": int(item.get("sky", 0)),
                "humidity": int(item.get("rhm", 0)),
                "rain_probability": int(item.get("pop", 0)),
            }
            key = (
                forecast["forecast_at"],
                forecast["spot_area_id"],
                forecast["spot_name"],
                forecast["temperature"],
                forecast["wind_direction"],
                forecast["wind_speed"],
                forecast["sky"],
                forecast["humidity"],
                forecast["rain_probability"],
            )
            grouped = grouped_forecasts.setdefault(key, forecast)
            theme = item.get("thema")
            if theme and theme not in grouped["themes"]:
                grouped["themes"].append(theme)

        forecasts = list(grouped_forecasts.values())
        for forecast in forecasts:
            forecast["themes"].sort()
        forecasts.sort(
            key=lambda item: (
                item["forecast_at"],
                item["spot_area_id"],
                item["spot_name"],
            )
        )
        return forecasts

    async def get_climate_index(
        self,
        city_area_id: str,
        base_time: str,
    ) -> dict[str, float | str]:
        cache_key = f"kma:climate:{city_area_id}:{base_time}"
        if cached := await cache.get(cache_key):
            return cached

        items = await self._request_items(
            "getCityTourClmIdx1",
            {
                "CURRENT_DATE": base_time,
                "DAY": 0,
                "CITY_AREA_ID": city_area_id,
            },
        )
        item = items[0]
        climate = {
            "score": float(item.get("kmaTci", 0)),
            "grade": item.get("TCI_GRADE", "정보없음"),
        }
        await cache.set(cache_key, climate, ttl=21600)
        return climate

    async def _request_items(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not settings.kma_service_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="KMA_SERVICE_KEY is not configured",
            )

        async with httpx.AsyncClient(
            timeout=settings.kma_timeout_seconds
        ) as client:
            request_params = {
                "ServiceKey": settings.kma_service_key,
                "pageNo": 1,
                "numOfRows": KMA_MAX_ROWS_PER_REQUEST,
                "dataType": "JSON",
                **params,
            }
            try:
                response = await client.get(
                    f"{settings.kma_base_url}/{endpoint}",
                    params=request_params,
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.TimeoutException as exc:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="KMA API request timed out",
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="KMA API communication failed",
                ) from exc

        api_response = payload.get("response", {})
        header = api_response.get("header", {})
        if header.get("resultCode") != "00":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "KMA API error: "
                    f"{header.get('resultMsg', 'unknown')}"
                ),
            )

        body = api_response.get("body", {})
        items = body.get("items", {}).get("item", [])
        total_count = int(body.get("totalCount", len(items)))
        if total_count > len(items):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"KMA returned {len(items)} of {total_count} rows. "
                    "Increase KMA_MAX_ROWS_PER_REQUEST."
                ),
            )

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data was not found",
            )
        return items


kma_client = KmaClient()
