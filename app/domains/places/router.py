from fastapi import APIRouter, Query

from app.domains.places.place import PlaceResult
from app.domains.places.services_tmap import search_tmap_places

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
    return await search_tmap_places(
        keyword=keyword,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )