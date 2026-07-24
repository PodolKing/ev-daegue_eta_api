from sqlalchemy.orm import Session

# Defaults per team agreement (§3.2)
DEFAULT_RADIUS_KM = 3.0
MAX_RADIUS_KM = 10.0
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def clamp_radius_km(radius_km: float) -> float:
    return max(0.1, min(radius_km, MAX_RADIUS_KM))


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


def list_stations_near(
    db: Session,
    *,
    lat: float,
    lng: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """
    TODO: bbox filter on idx_lat_lng → Haversine → aggregate by stat_id
    → LEFT JOIN status → availableCount (status '2' only; null if no valid status)
    → sort by distanceKm ASC → limit
    """
    _ = (db, lat, lng, radius_km, limit)
    raise NotImplementedError("stations service: implement DB query (see docs/stations_api.md)")
