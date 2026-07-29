import math
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


DEFAULT_RADIUS_KM = 3.0
MAX_RADIUS_KM = 10.0
DEFAULT_LIMIT = 50
MAX_LIMIT = 200

def clamp_radius_km(radius_km: float) -> float:
    return max(0.1, min(radius_km, MAX_RADIUS_KM))


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


def _as_float(value: object) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)  # type: ignore[arg-type]


def _nullable_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _split_charger_types(value: object) -> list[str]:
    """GROUP_CONCAT(DISTINCT chger_type) → code list (e.g. ['02','04'])."""
    if value is None:
        return []
    text_value = str(value).strip()
    if not text_value:
        return []
    return [part for part in text_value.split(",") if part]


def _station_row(row) -> dict:
    return {
        "station_id": row["station_id"],
        "name": row["name"],
        "address": row["address"],
        "lat": _as_float(row["lat"]),
        "lng": _as_float(row["lng"]),
        "available_count": _nullable_int(row["available_count"]),
        "available_count_other": _nullable_int(row["available_count_other"]),
        "available_count_slow": _nullable_int(row["available_count_slow"]),
        "distance_km": (
            round(_as_float(row["distance_km"]), 3)
            if "distance_km" in row and row["distance_km"] is not None
            else None
        ),
        "charger_total": _nullable_int(row["charger_total"]),
        "charger_total_other": _nullable_int(row["charger_total_other"]),
        "charger_types": _split_charger_types(row["charger_types"]),
        "source_mode": "LIVE",
    }


# status='2' 집계 / 관측 없음 → NULL (null ≠ 0)
# 그외: chger_type NOT IN (02,08) 또는 NULL/미상 → other
_AVAIL_SQL = """
            CASE
                WHEN SUM(
                    CASE
                        WHEN s.charger_status IN ('1','2','3','4','5','9')
                        THEN 1 ELSE 0
                    END
                ) = 0 THEN NULL
                ELSE SUM(
                    CASE
                        WHEN s.charger_status = '2'
                        THEN 1 ELSE 0
                    END
                )
            END AS available_count,

            CASE
                WHEN SUM(
                    CASE
                        WHEN IFNULL(i.chger_type, '') NOT IN ('02','08')
                         AND s.charger_status IN ('1','2','3','4','5','9')
                        THEN 1 ELSE 0
                    END
                ) = 0 THEN NULL
                ELSE SUM(
                    CASE
                        WHEN IFNULL(i.chger_type, '') NOT IN ('02','08')
                         AND s.charger_status = '2'
                        THEN 1 ELSE 0
                    END
                )
            END AS available_count_other,

            CASE
                WHEN SUM(
                    CASE
                        WHEN i.chger_type IN ('02','08')
                         AND s.charger_status IN ('1','2','3','4','5','9')
                        THEN 1 ELSE 0
                    END
                ) = 0 THEN NULL
                ELSE SUM(
                    CASE
                        WHEN i.chger_type IN ('02','08')
                         AND s.charger_status = '2'
                        THEN 1 ELSE 0
                    END
                )
            END AS available_count_slow
"""

# 총대수: 전체 + 그외(완속 02/08 제외, 타입 공란→other). 완속 총 = total − other
_TOTAL_SQL = """
            COUNT(DISTINCT i.chger_id) AS charger_total,

            COUNT(DISTINCT CASE
                WHEN IFNULL(i.chger_type, '') NOT IN ('02', '08')
                THEN i.chger_id
            END) AS charger_total_other
"""


def list_stations_near(
    db: Session,
    *,
    lat: float,
    lng: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """
    좌표 기준 직선거리 반경 내 충전소 조회
    """

    radius_km = clamp_radius_km(radius_km)
    limit = clamp_limit(limit)

    lat_delta = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))

    lng_delta = (
        radius_km / (111.0 * abs(cos_lat))
        if abs(cos_lat) > 1e-6
        else radius_km / 111.0
    )

    min_lat = lat - lat_delta
    max_lat = lat + lat_delta
    min_lng = lng - lng_delta
    max_lng = lng + lng_delta

    sql = text(
        f"""
        SELECT
            i.stat_id AS station_id,
            MAX(i.stat_nm) AS name,
            MAX(i.addr) AS address,
            MAX(i.lat) AS lat,
            MAX(i.lng) AS lng,

            (
                6371 * ACOS(
                    LEAST(
                        1,
                        GREATEST(
                            -1,
                            COS(RADIANS(:lat))
                            * COS(RADIANS(MAX(i.lat)))
                            * COS(RADIANS(MAX(i.lng)) - RADIANS(:lng))
                            + SIN(RADIANS(:lat))
                            * SIN(RADIANS(MAX(i.lat)))
                        )
                    )
                )
            ) AS distance_km,

{_AVAIL_SQL},

{_TOTAL_SQL},

            GROUP_CONCAT(DISTINCT i.chger_type ORDER BY i.chger_type) AS charger_types

        FROM ev_charger_info AS i

        LEFT JOIN ev_charger_status AS s
            ON i.stat_id = s.stat_id
           AND i.chger_id = s.chger_id

        WHERE i.lat IS NOT NULL
          AND i.lng IS NOT NULL
          AND i.lat BETWEEN :min_lat AND :max_lat
          AND i.lng BETWEEN :min_lng AND :max_lng

        GROUP BY i.stat_id

        HAVING distance_km <= :radius_km

        ORDER BY distance_km ASC

        LIMIT :limit
        """
    )

    rows = db.execute(
        sql,
        {
            "lat": lat,
            "lng": lng,
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
            "radius_km": radius_km,
            "limit": limit,
        },
    ).mappings().all()

    return [_station_row(row) for row in rows]


def list_stations_viewport(
    db: Session,
    *,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """
    지도 화면 영역(bbox) 내 충전소 조회
    """

    limit = clamp_limit(limit)

    sql = text(
        f"""
        SELECT
            i.stat_id AS station_id,
            MAX(i.stat_nm) AS name,
            MAX(i.addr) AS address,
            MAX(i.lat) AS lat,
            MAX(i.lng) AS lng,

{_AVAIL_SQL},

{_TOTAL_SQL},

            GROUP_CONCAT(DISTINCT i.chger_type ORDER BY i.chger_type) AS charger_types

        FROM ev_charger_info AS i

        LEFT JOIN ev_charger_status AS s
            ON i.stat_id = s.stat_id
           AND i.chger_id = s.chger_id

        WHERE i.lat IS NOT NULL
          AND i.lng IS NOT NULL
          AND i.lat BETWEEN :min_lat AND :max_lat
          AND i.lng BETWEEN :min_lng AND :max_lng

        GROUP BY i.stat_id

        ORDER BY i.stat_id

        LIMIT :limit
        """
    )

    rows = db.execute(
        sql,
        {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
            "limit": limit,
        },
    ).mappings().all()

    return [_station_row(row) for row in rows]
