from app.domains.places.client import fetch_tmap_places
from app.domains.places.place import PlaceResult


async def search_places(
    keyword: str,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
) -> list[PlaceResult]:
    # client 함수로 인자 전달
    results = await fetch_tmap_places(
        keyword=keyword,
        center_lat=lat,
        center_lng=lng,
        radius_km=radius_km,
    )

    return [
        PlaceResult(
            id=str(item["id"]),
            name=item["name"] or "",
            address=item["address"] or "",
            lat=float(item["lat"]),
            lng=float(item["lng"]),
        )
        for item in results
        if item.get("id") is not None
        and item.get("lat") is not None
        and item.get("lng") is not None
    ]