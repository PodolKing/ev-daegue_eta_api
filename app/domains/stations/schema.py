from app.schemas.base import CamelModel


class StationItem(CamelModel):
    station_id: str
    name: str | None = None
    address: str | None = None
    lat: float
    lng: float
    available_count: int | None = None
    distance_km: float | None = None
    charger_total: int | None = None
    source_mode: str = "LIVE"


class StationListResponse(CamelModel):
    items: list[StationItem]
    radius_km: float
    limit: int
    count: int
