import json
import math
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

DEFAULT_RADIUS_KM = 3.0
MAX_RADIUS_KM = 10.0
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
SEARCH_MIN_Q_LEN = 2
SEARCH_DEFAULT_LIMIT = 20
SEARCH_MAX_LIMIT = 30

def clamp_radius_km(radius_km: float) -> float:
    return max(0.1, min(radius_km, MAX_RADIUS_KM))


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


def clamp_search_limit(limit: int) -> int:
    return max(1, min(limit, SEARCH_MAX_LIMIT))


def _like_contains(q: str) -> str:
    """사용자 입력의 LIKE 와일드카드는 제거. 전체 dump 방지용 contains."""
    cleaned = q.replace("\\", "").replace("%", "").replace("_", "").strip()
    return f"%{cleaned}%"


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


def _json_get(item: dict, snake: str, camel: str) -> object:
    if snake in item:
        return item[snake]
    if camel in item:
        return item[camel]
    return None


def _parse_chargers(value: object) -> list[dict]:
    """JSON_ARRAYAGG / JSONB_AGG → ChargerItem dict list (snake_case)."""
    if value is None:
        return []
    # psycopg2 may return list/memoryview for jsonb
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        text_value = value.strip()
        if not text_value:
            return []
        try:
            value = json.loads(text_value)
        except json.JSONDecodeError:
            return []
    if not isinstance(value, list):
        return []

    out: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        chger_id = _json_get(item, "chger_id", "chgerId")
        if chger_id is None or str(chger_id).strip() == "":
            continue
        out.append(
            {
                "chger_id": str(chger_id),
                "stat_nm": _nullable_str(_json_get(item, "stat_nm", "statNm")),
                "chger_type": _nullable_str(
                    _json_get(item, "chger_type", "chgerType")
                ),
                "addr": _nullable_str(_json_get(item, "addr", "addr")),
                "addr_detail": _nullable_str(
                    _json_get(item, "addr_detail", "addrDetail")
                ),
                "location": _nullable_str(_json_get(item, "location", "location")),
                "lat": _nullable_float(_json_get(item, "lat", "lat")),
                "lng": _nullable_float(_json_get(item, "lng", "lng")),
                "use_time": _nullable_str(_json_get(item, "use_time", "useTime")),
                "busi_id": _nullable_str(_json_get(item, "busi_id", "busiId")),
                "bnm": _nullable_str(_json_get(item, "bnm", "bnm")),
                "busi_nm": _nullable_str(_json_get(item, "busi_nm", "busiNm")),
                "busi_call": _nullable_str(_json_get(item, "busi_call", "busiCall")),
                "output": _nullable_float(_json_get(item, "output", "output")),
                "method": _nullable_str(_json_get(item, "method", "method")),
                "zcode": _nullable_str(_json_get(item, "zcode", "zcode")),
                "zscode": _nullable_str(_json_get(item, "zscode", "zscode")),
                "kind": _nullable_str(_json_get(item, "kind", "kind")),
                "kind_detail": _nullable_str(
                    _json_get(item, "kind_detail", "kindDetail")
                ),
                "parking_free": _nullable_str(
                    _json_get(item, "parking_free", "parkingFree")
                ),
                "note": _nullable_str(_json_get(item, "note", "note")),
                "limit_yn": _nullable_str(_json_get(item, "limit_yn", "limitYn")),
                "limit_detail": _nullable_str(
                    _json_get(item, "limit_detail", "limitDetail")
                ),
                "del_yn": _nullable_str(_json_get(item, "del_yn", "delYn")),
                "del_detail": _nullable_str(
                    _json_get(item, "del_detail", "delDetail")
                ),
                "traffic_yn": _nullable_str(
                    _json_get(item, "traffic_yn", "trafficYn")
                ),
                "install_year": _nullable_str(
                    _json_get(item, "install_year", "installYear")
                ),
                "floor_num": _nullable_str(_json_get(item, "floor_num", "floorNum")),
                "floor_type": _nullable_str(
                    _json_get(item, "floor_type", "floorType")
                ),
                "info_updated_at": _nullable_str(
                    _json_get(item, "info_updated_at", "infoUpdatedAt")
                ),
                "charger_status": _nullable_str(
                    _json_get(item, "charger_status", "chargerStatus")
                ),
                "last_updated": _nullable_str(
                    _json_get(item, "last_updated", "lastUpdated")
                ),
            }
        )

    out.sort(key=lambda row: row["chger_id"])
    return out


# info 전 컬럼 + status 스냅샷 → 소 단위 JSON 배열 (목록 중첩)
_CHARGERS_SQL_MYSQL = """
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'chger_id', i.chger_id,
                    'stat_nm', i.stat_nm,
                    'chger_type', i.chger_type,
                    'addr', i.addr,
                    'addr_detail', i.addr_detail,
                    'location', i.location,
                    'lat', i.lat,
                    'lng', i.lng,
                    'use_time', i.use_time,
                    'busi_id', i.busi_id,
                    'bnm', i.bnm,
                    'busi_nm', i.busi_nm,
                    'busi_call', i.busi_call,
                    'output', i.output,
                    'method', i.method,
                    'zcode', i.zcode,
                    'zscode', i.zscode,
                    'kind', i.kind,
                    'kind_detail', i.kind_detail,
                    'parking_free', i.parking_free,
                    'note', i.note,
                    'limit_yn', i.limit_yn,
                    'limit_detail', i.limit_detail,
                    'del_yn', i.del_yn,
                    'del_detail', i.del_detail,
                    'traffic_yn', i.traffic_yn,
                    'install_year', i.install_year,
                    'floor_num', i.floor_num,
                    'floor_type', i.floor_type,
                    'info_updated_at', DATE_FORMAT(i.updated_at, '%Y-%m-%dT%H:%i:%s'),
                    'charger_status', s.charger_status,
                    'last_updated', DATE_FORMAT(s.last_updated, '%Y-%m-%dT%H:%i:%s')
                )
            ) AS chargers_json
"""

_CHARGERS_SQL_PG = """
            JSONB_AGG(
                JSONB_BUILD_OBJECT(
                    'chger_id', i.chger_id,
                    'stat_nm', i.stat_nm,
                    'chger_type', i.chger_type,
                    'addr', i.addr,
                    'addr_detail', i.addr_detail,
                    'location', i.location,
                    'lat', i.lat,
                    'lng', i.lng,
                    'use_time', i.use_time,
                    'busi_id', i.busi_id,
                    'bnm', i.bnm,
                    'busi_nm', i.busi_nm,
                    'busi_call', i.busi_call,
                    'output', i.output,
                    'method', i.method,
                    'zcode', i.zcode,
                    'zscode', i.zscode,
                    'kind', i.kind,
                    'kind_detail', i.kind_detail,
                    'parking_free', i.parking_free,
                    'note', i.note,
                    'limit_yn', i.limit_yn,
                    'limit_detail', i.limit_detail,
                    'del_yn', i.del_yn,
                    'del_detail', i.del_detail,
                    'traffic_yn', i.traffic_yn,
                    'install_year', i.install_year,
                    'floor_num', i.floor_num,
                    'floor_type', i.floor_type,
                    'info_updated_at', TO_CHAR(i.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                    'charger_status', s.charger_status,
                    'last_updated', TO_CHAR(s.last_updated, 'YYYY-MM-DD"T"HH24:MI:SS')
                )
                ORDER BY i.chger_id
            ) AS chargers_json
"""


def _nullable_float(value: object) -> float | None:
    if value is None:
        return None
    return _as_float(value)


def _nullable_str(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


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
        "chargers": _parse_chargers(row.get("chargers_json")),
        "use_time": _nullable_str(row.get("use_time")),
        "busi_nm": _nullable_str(row.get("busi_nm")),
        "busi_call": _nullable_str(row.get("busi_call")),
        "output_min": _nullable_float(row.get("output_min")),
        "output_max": _nullable_float(row.get("output_max")),
        "limit_detail": _nullable_str(row.get("limit_detail")),
        "traffic_yn": _nullable_str(row.get("traffic_yn")),
        "parking_free": _nullable_str(row.get("parking_free")),
        "source_mode": "LIVE",
    }


# status='2' 집계 / 관측 없음 → NULL (null ≠ 0)
# 그외: chger_type NOT IN (02,08) 또는 NULL/미상 → other
_AVAIL_SQL_MYSQL = """
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

_AVAIL_SQL_PG = """
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
                        WHEN COALESCE(i.chger_type, '') NOT IN ('02','08')
                         AND s.charger_status IN ('1','2','3','4','5','9')
                        THEN 1 ELSE 0
                    END
                ) = 0 THEN NULL
                ELSE SUM(
                    CASE
                        WHEN COALESCE(i.chger_type, '') NOT IN ('02','08')
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
_TOTAL_SQL_MYSQL = """
            COUNT(DISTINCT i.chger_id) AS charger_total,

            COUNT(DISTINCT CASE
                WHEN IFNULL(i.chger_type, '') NOT IN ('02', '08')
                THEN i.chger_id
            END) AS charger_total_other
"""

_TOTAL_SQL_PG = """
            COUNT(DISTINCT i.chger_id) AS charger_total,

            COUNT(DISTINCT CASE
                WHEN COALESCE(i.chger_type, '') NOT IN ('02', '08')
                THEN i.chger_id
            END) AS charger_total_other
"""

_TYPES_SQL_MYSQL = """
            GROUP_CONCAT(DISTINCT i.chger_type ORDER BY i.chger_type) AS charger_types
"""

_TYPES_SQL_PG = """
            STRING_AGG(DISTINCT i.chger_type, ',' ORDER BY i.chger_type) AS charger_types
"""


def _dialect_sql(db: Session) -> tuple[str, str, str, str]:
    """환경변수가 아닌 실제 SQLAlchemy 연결 dialect로 SQL 조각을 선택한다."""
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return _AVAIL_SQL_PG, _TOTAL_SQL_PG, _TYPES_SQL_PG, _CHARGERS_SQL_PG
    if dialect in {"mysql", "mariadb"}:
        return (
            _AVAIL_SQL_MYSQL,
            _TOTAL_SQL_MYSQL,
            _TYPES_SQL_MYSQL,
            _CHARGERS_SQL_MYSQL,
        )
    raise RuntimeError(f"지원하지 않는 DB dialect: {dialect}")


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

    avail_sql, total_sql, types_sql, chargers_sql = _dialect_sql(db)

    # Postgres: HAVING cannot use SELECT aliases → wrap and filter outer
    sql = text(
        f"""
        SELECT *
        FROM (
            SELECT
                i.stat_id AS station_id,
                MAX(i.stat_nm) AS name,
                MAX(i.addr) AS address,
                MAX(i.lat) AS lat,
                MAX(i.lng) AS lng,
                MAX(i.use_time) AS use_time,
                MAX(i.busi_nm) AS busi_nm,
                MAX(i.busi_call) AS busi_call,
                MIN(i.output) AS output_min,
                MAX(i.output) AS output_max,
                MAX(i.limit_detail) AS limit_detail,
                MAX(i.traffic_yn) AS traffic_yn,
                MAX(i.parking_free) AS parking_free,

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

{avail_sql},

{total_sql},

{types_sql},

{chargers_sql}

            FROM ev_charger_info AS i

            LEFT JOIN ev_charger_status AS s
                ON i.stat_id = s.stat_id
               AND i.chger_id = s.chger_id

            WHERE i.lat IS NOT NULL
              AND i.lng IS NOT NULL
              AND i.lat BETWEEN :min_lat AND :max_lat
              AND i.lng BETWEEN :min_lng AND :max_lng

            GROUP BY i.stat_id
        ) AS near_stations
        WHERE distance_km <= :radius_km
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

    avail_sql, total_sql, types_sql, chargers_sql = _dialect_sql(db)

    sql = text(
        f"""
        SELECT
            i.stat_id AS station_id,
            MAX(i.stat_nm) AS name,
            MAX(i.addr) AS address,
            MAX(i.lat) AS lat,
            MAX(i.lng) AS lng,
            MAX(i.use_time) AS use_time,
            MAX(i.busi_nm) AS busi_nm,
            MAX(i.busi_call) AS busi_call,
            MIN(i.output) AS output_min,
            MAX(i.output) AS output_max,
            MAX(i.limit_detail) AS limit_detail,
            MAX(i.traffic_yn) AS traffic_yn,
            MAX(i.parking_free) AS parking_free,

{avail_sql},

{total_sql},

{types_sql},

{chargers_sql}

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


_AVAIL_COUNT_SQL = """
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
            END AS available_count
"""


def search_stations(
    db: Session,
    *,
    q: str,
    limit: int = SEARCH_DEFAULT_LIMIT,
) -> list[dict]:
    """
    충전소명·주소 키워드 검색. stat_id 집계.
    반경 API와 분리. 전체 테이블 dump 없음 (q 최소 길이 + limit).
    """
    query = q.strip()
    limit = clamp_search_limit(limit)
    if len(query) < SEARCH_MIN_Q_LEN:
        return []

    pattern = _like_contains(query)
    if pattern == "%%":
        return []

    dialect = db.get_bind().dialect.name
    like_op = "ILIKE" if dialect == "postgresql" else "LIKE"

    sql = text(
        f"""
        SELECT
            i.stat_id AS station_id,
            MAX(i.stat_nm) AS name,
            MAX(i.addr) AS address,
            MAX(i.lat) AS lat,
            MAX(i.lng) AS lng,
{_AVAIL_COUNT_SQL}
        FROM ev_charger_info AS i
        LEFT JOIN ev_charger_status AS s
            ON i.stat_id = s.stat_id
           AND i.chger_id = s.chger_id
        WHERE i.lat IS NOT NULL
          AND i.lng IS NOT NULL
          AND (
                i.stat_nm {like_op} :pattern
             OR i.addr {like_op} :pattern
             OR i.addr_detail {like_op} :pattern
          )
        GROUP BY i.stat_id
        ORDER BY MAX(i.stat_nm) ASC, i.stat_id ASC
        LIMIT :limit
        """
    )

    rows = db.execute(sql, {"pattern": pattern, "limit": limit}).mappings().all()

    out: list[dict] = []
    for row in rows:
        if row["lat"] is None or row["lng"] is None:
            continue
        out.append(
            {
                "station_id": row["station_id"],
                "name": _nullable_str(row["name"]),
                "address": _nullable_str(row["address"]),
                "lat": _as_float(row["lat"]),
                "lng": _as_float(row["lng"]),
                "available_count": _nullable_int(row["available_count"]),
            }
        )
    return out

