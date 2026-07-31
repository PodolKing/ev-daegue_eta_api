from fastapi import HTTPException

from app.domains.routes.client import fetch_tmap_car_route
from app.domains.routes.schema import CarRouteRequest, CarRouteResponse, RoutePoint


async def get_car_route(body: CarRouteRequest) -> CarRouteResponse:
    """TMAP raw → distanceM / durationSec / path 정규화."""
    raw = await fetch_tmap_car_route(
        start_lat=body.start_lat,
        start_lng=body.start_lng,
        end_lat=body.end_lat,
        end_lng=body.end_lng,
        start_name=body.start_name or "현위치",
        end_name=body.end_name or "도착지",
    )

    features = raw.get("features") or []
    if not features:
        raise HTTPException(status_code=502, detail="TMAP route: empty features")

    props = features[0].get("properties") or {}
    # TMAP: totalDistance(m), totalTime(sec)
    distance_m = int(props.get("totalDistance") or 0)
    duration_sec = int(props.get("totalTime") or 0)

    path: list[RoutePoint] = []
    for f in features:
        geom = f.get("geometry") or {}
        if geom.get("type") != "LineString":
            continue
        for coord in geom.get("coordinates") or []:
            if len(coord) < 2:
                continue
            lng, lat = coord[0], coord[1]
            path.append(RoutePoint(lat=float(lat), lng=float(lng)))

    if not path:
        raise HTTPException(status_code=502, detail="TMAP route: no path")

    return CarRouteResponse(
        distance_m=distance_m,
        duration_sec=duration_sec,
        path=path,
    )
