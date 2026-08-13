from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db, is_db_configured
from app.domains.stations import controller as stations_controller
from app.domains.stations.schema import StationListResponse, StationSearchResponse
from app.domains.stations.service import (
    DEFAULT_LIMIT,
    DEFAULT_RADIUS_KM,
    MAX_LIMIT,
    SEARCH_DEFAULT_LIMIT,
    SEARCH_MAX_LIMIT,
    SEARCH_MIN_Q_LEN,
    clamp_limit,
    clamp_radius_km,
)

router = APIRouter(prefix="/api/v1/stations", tags=["stations"])


@router.get("", response_model=StationListResponse)
def list_stations(
    lat: float = Query(..., description="Current latitude"),
    lng: float = Query(..., description="Current longitude"),
    radius_km: float = Query(DEFAULT_RADIUS_KM, ge=0.1, le=10),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    db: Session | None = Depends(get_db),
) -> StationListResponse:
    """Nearby stations by straight-line distance (DB Haversine, not TMAP)."""
    if not is_db_configured() or db is None:
        return StationListResponse(
            items=[],
            radius_km=clamp_radius_km(radius_km),
            limit=clamp_limit(limit),
            count=0,
        )

    return stations_controller.get_stations(
        db, lat=lat, lng=lng, radius_km=radius_km, limit=limit
    )


@router.get("/search", response_model=StationSearchResponse)
def search_stations(
    q: str = Query(
        ...,
        min_length=SEARCH_MIN_Q_LEN,
        max_length=100,
        description="충전소명·주소 키워드",
    ),
    limit: int = Query(SEARCH_DEFAULT_LIMIT, ge=1, le=SEARCH_MAX_LIMIT),
    db: Session | None = Depends(get_db),
) -> StationSearchResponse:
    """충전소명·주소 키워드 검색. 반경 목록과 별도. dump 금지(q 2자+, limit)."""
    query = q.strip()
    if not is_db_configured() or db is None:
        return StationSearchResponse(
            items=[],
            query=query,
            limit=limit,
            count=0,
        )

    return stations_controller.search_stations(db, q=query, limit=limit)
