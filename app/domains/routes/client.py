"""TMAP 자동차 경로 REST 호출."""

from urllib.parse import quote

import httpx
from fastapi import HTTPException

from app.core.config import get_settings

# POST https://apis.openapi.sk.com/tmap/routes?version=1
TMAP_ROUTES_URL = "https://apis.openapi.sk.com/tmap/routes"


async def fetch_tmap_car_route(
    *,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    start_name: str = "현위치",
    end_name: str = "도착지",
) -> dict:
    """POST /tmap/routes — raw JSON. 정규화는 services."""
    app_key = get_settings().tmap_app_key
    if not app_key:
        raise HTTPException(status_code=503, detail="TMAP_APP_KEY not configured")

    headers = {
        "appKey": app_key,
        "Content-Type": "application/json",
    }
    # startName/endName: TMAP 문서 — UTF-8 URL 인코딩
    body = {
        "startX": start_lng,
        "startY": start_lat,
        "endX": end_lng,
        "endY": end_lat,
        "startName": quote(start_name or "현위치"),
        "endName": quote(end_name or "도착지"),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TMAP_ROUTES_URL,
            params={"version": "1"},
            headers=headers,
            json=body,
            timeout=10,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"TMAP car route failed ({response.status_code})",
        )

    return response.json()
