from sqlalchemy.orm import Session

from app.domains.stations import service as stations_service
from app.domains.stations.schema import StationItem, StationListResponse


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
