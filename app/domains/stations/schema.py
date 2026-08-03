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
    charger_total_other: int | None = None
    charger_types: list[str] = []
    use_time: str | None = None
    busi_nm: str | None = None
    busi_call: str | None = None
    output_min: float | None = None
    output_max: float | None = None
    limit_detail: str | None = None
    traffic_yn: str | None = None
    parking_free: str | None = None
    source_mode: str = "LIVE"


class StationListResponse(CamelModel):
    items: list[StationItem]
    radius_km: float
    limit: int
    count: int
