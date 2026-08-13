from sqlalchemy.orm import Session

from app.domains.stations import service as stations_service
from app.domains.stations.schema import (
    StationItem,
    StationListResponse,
    StationSearchItem,
    StationSearchResponse,
)


def get_stations(
    db: Session,
    *,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
) -> StationListResponse:
    """현위치 기준 반경(near) 충전소 조회."""
    radius = stations_service.clamp_radius_km(radius_km)
    lim = stations_service.clamp_limit(limit)

    rows = stations_service.list_stations_near(
        db, lat=lat, lng=lng, radius_km=radius, limit=lim
    )

    items = [StationItem.model_validate(row) for row in rows]
    return StationListResponse(
        items=items,
        radius_km=radius,
        limit=lim,
        count=len(items),
    )


def search_stations(
    db: Session,
    *,
    q: str,
    limit: int,
) -> StationSearchResponse:
    """충전소명·주소 키워드 검색."""
    query = q.strip()
    lim = stations_service.clamp_search_limit(limit)
    if len(query) < stations_service.SEARCH_MIN_Q_LEN:
        return StationSearchResponse(items=[], query=query, limit=lim, count=0)

    rows = stations_service.search_stations(db, q=query, limit=lim)
    items = [StationSearchItem.model_validate(row) for row in rows]
    return StationSearchResponse(
        items=items,
        query=query,
        limit=lim,
        count=len(items),
    )
