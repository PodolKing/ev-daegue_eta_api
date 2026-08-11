from fastapi import APIRouter, Query

from app.domains.places.place import PlaceResult
from app.domains.places.services import (
    search_places as search_places_service,
    search_places_around as search_places_around_service,
)

router = APIRouter(
    prefix="/api/v1/places",
    tags=["places"],
)


@router.get("/search", response_model=list[PlaceResult])
async def search_places(
    keyword: str = Query(..., min_length=1),
    lat: float | None = Query(None, description="위도"),
    lng: float | None = Query(None, description="경도"),
    radius_km: float | None = Query(None, description="검색 반경 (km)"),
) -> list[PlaceResult]:
    return await search_places_service(
        keyword=keyword,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )


@router.get("/around", response_model=list[PlaceResult])
async def search_places_around(
    categories: str = Query(..., min_length=1, description="TMAP 업종명 (예: 카페)"),
    lat: float = Query(..., description="중심 위도"),
    lng: float = Query(..., description="중심 경도"),
    radius_km: float = Query(1, ge=1, le=33, description="검색 반경 (km, 1~33)"),
    count: int = Query(
        50,
        ge=1,
        le=200,
        description="최대 결과 수 (UI: 1km→50 / 2km→100 / 3km→150)",
    ),
) -> list[PlaceResult]:
    return await search_places_around_service(
        categories=categories,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        count=count,
    )
