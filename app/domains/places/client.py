import httpx
from fastapi import HTTPException

from app.core.config import get_settings

TMAP_URL = "https://apis.openapi.sk.com/tmap/pois"


async def fetch_tmap_places(
    keyword: str,
    center_lat: float | None = None,
    center_lng: float | None = None,
    radius_km: float | None = None,
) -> list[dict]:
    app_key = get_settings().tmap_app_key
    if not app_key:
        raise HTTPException(status_code=503, detail="TMAP_APP_KEY not configured")

    headers = {"appKey": app_key}
    
    # 기본 검색 파라미터
    params: dict[str, str | int | float] = {
        "version": "1",
        "searchKeyword": keyword,
        "count": 10,
    }

    # 위치 정보 및 반경 값이 전달되었을 경우 Tmap 위치 기준 검색 파라미터 추가
    if center_lat is not None and center_lng is not None:
        params["centerLat"] = center_lat
        params["centerLon"] = center_lng
        # Tmap API는 radius 파라미터를 km 단위로 받음 (예: 3, 5, 10)
        if radius_km is not None:
            params["radius"] = radius_km
            params["searchtypCd"] = "R"  # R: 반경 검색(Radius) 옵션

    async with httpx.AsyncClient() as client:
        response = await client.get(
            TMAP_URL,
            headers=headers,
            params=params,
            timeout=5,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"TMAP places search failed ({response.status_code})",
        )

    data = response.json()
    pois = (
        data.get("searchPoiInfo", {})
        .get("pois", {})
        .get("poi", [])
    )
    if isinstance(pois, dict):
        pois = [pois]

    return [
        {
            "id": poi.get("id"),
            "name": poi.get("name"),
            "address": " ".join(
                filter(
                    None,
                    [
                        poi.get("upperAddrName"),
                        poi.get("middleAddrName"),
                        poi.get("lowerAddrName"),
                    ],
                )
            ),
            "lat": poi.get("noorLat"),
            "lng": poi.get("noorLon"),
        }
        for poi in pois
    ]