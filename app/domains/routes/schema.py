from app.schemas.base import CamelModel


class CarRouteRequest(CamelModel):
    """자동차 경로 요청 — 출발=현위치, 도착=장소/충전소."""

    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    start_name: str | None = "현위치"
    end_name: str | None = "도착지"


class RoutePoint(CamelModel):
    lat: float
    lng: float


class CarRouteResponse(CamelModel):
    """정규화된 경로 — FE polyline / ETA용."""

    distance_m: int
    duration_sec: int
    path: list[RoutePoint]
