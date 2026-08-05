from app.schemas.base import CamelModel





class ChargerItem(CamelModel):

    """충전기 1대 — info 행 + status 스냅샷. 목록 중첩·패널·로그 조인용."""



    chger_id: str

    # --- ev_charger_info ---

    stat_nm: str | None = None

    chger_type: str | None = None

    addr: str | None = None

    addr_detail: str | None = None

    location: str | None = None

    lat: float | None = None

    lng: float | None = None

    use_time: str | None = None

    busi_id: str | None = None

    bnm: str | None = None

    busi_nm: str | None = None

    busi_call: str | None = None

    output: float | None = None

    method: str | None = None

    zcode: str | None = None

    zscode: str | None = None

    kind: str | None = None

    kind_detail: str | None = None

    parking_free: str | None = None

    note: str | None = None

    limit_yn: str | None = None

    limit_detail: str | None = None

    del_yn: str | None = None

    del_detail: str | None = None

    traffic_yn: str | None = None

    install_year: str | None = None

    floor_num: str | None = None

    floor_type: str | None = None

    info_updated_at: str | None = None

    # --- ev_charger_status ---

    charger_status: str | None = None

    last_updated: str | None = None





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

    # 충전기 단위 (stat_id 집계 유지 + 중첩). FE는 아직 미표시해도 됨.

    chargers: list[ChargerItem] = []

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


