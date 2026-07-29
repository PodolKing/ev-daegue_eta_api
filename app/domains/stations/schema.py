from app.schemas.base import CamelModel


class StationItem(CamelModel):
    station_id: str
    name: str | None = None
    address: str | None = None
    lat: float
    lng: float
    available_count: int | None = None
    available_count_other: int | None = None
    available_count_slow: int | None = None
    distance_km: float | None = None
    charger_total: int | None = None
    charger_types: list[str] = []
    source_mode: str = "LIVE"


class StationListResponse(CamelModel):
    items: list[StationItem]
    radius_km: float
    limit: int
    count: int
