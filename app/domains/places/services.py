from app.domains.places.client import fetch_tmap_around_places, fetch_tmap_places
from app.domains.places.place import PlaceResult


def _to_place_results(results: list[dict]) -> list[PlaceResult]:
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


async def search_places(
    keyword: str,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
) -> list[PlaceResult]:
    results = await fetch_tmap_places(
        keyword=keyword,
        center_lat=lat,
        center_lng=lng,
        radius_km=radius_km,
    )
    return _to_place_results(results)


async def search_places_around(
    categories: str,
    lat: float,
    lng: float,
    radius_km: float = 1,
    count: int = 50,
) -> list[PlaceResult]:
    results = await fetch_tmap_around_places(
        categories=categories,
        center_lat=lat,
        center_lng=lng,
        radius_km=radius_km,
        count=count,
    )
    return _to_place_results(results)