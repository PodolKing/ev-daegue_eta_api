# 즐겨찾기 비즈니스 로직
# 충전소 단위 등록/해제, 전체 조회, 최대 10개 제한을 담당한다.
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.auth.models import User

from .models import UserFavoriteStation
from .schema import FavoriteSort


MAX_FAVORITES = 10


def _now() -> datetime:
    """PostgreSQL TIMESTAMP 컬럼에 저장할 UTC 기준 naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _favorite_count(db: Session, *, user_pk: int) -> int:
    """사용자의 현재 즐겨찾기 개수."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(UserFavoriteStation)
            .where(UserFavoriteStation.user_id == user_pk)
        )
        or 0
    )


def _station_exists(db: Session, *, station_id: str) -> bool:
    """
    stat_id는 DB FK가 아니므로 애플리케이션에서 존재 여부를 확인한다.
    ev_charger_info는 충전기별 행이므로 한 행만 확인한다.
    """
    value = db.execute(
        text(
            """
            SELECT 1
            FROM ev_charger_info
            WHERE stat_id = :station_id
            LIMIT 1
            """
        ),
        {"station_id": station_id},
    ).scalar_one_or_none()
    return value is not None


def _lock_user(db: Session, *, user_pk: int) -> None:
    """같은 사용자의 동시 등록/해제를 직렬화한다."""
    user_exists = db.execute(
        select(User.id).where(User.id == user_pk).with_for_update()
    ).scalar_one_or_none()
    if user_exists is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")


def _normalize_station_id(station_id: str) -> str:
    station_key = station_id.strip()
    if not station_key:
        raise HTTPException(status_code=400, detail="stationId는 필수입니다")
    return station_key


def is_favorite(db: Session, *, user_pk: int, station_id: str) -> bool:
    """특정 충전소의 즐겨찾기 등록 여부."""
    favorite_id = db.scalar(
        select(UserFavoriteStation.id).where(
            UserFavoriteStation.user_id == user_pk,
            UserFavoriteStation.stat_id == station_id,
        )
    )
    return favorite_id is not None


def toggle_favorite(
    db: Session,
    *,
    user_pk: int,
    station_id: str,
    memo: str | None,
) -> dict[str, object]:
    """
    별 마크 토글.

    - 등록 상태면 행을 삭제한다.
    - 미등록이면 최대 10개와 충전소 존재 여부를 확인한 뒤 등록한다.
    - memo는 신규 등록에만 적용한다.
    - 10개 제한은 HTTP 오류가 아니라 processed=false 결과로 반환한다.
    """
    station_key = _normalize_station_id(station_id)
    memo_value = (memo or "").strip() or None

    try:
        _lock_user(db, user_pk=user_pk)

        favorite = db.scalar(
            select(UserFavoriteStation).where(
                UserFavoriteStation.user_id == user_pk,
                UserFavoriteStation.stat_id == station_key,
            )
        )
        if favorite is not None:
            db.delete(favorite)
            db.flush()
            count = _favorite_count(db, user_pk=user_pk)
            db.commit()
            return {
                "processed": True,
                "is_favorite": False,
                "favorite_count": count,
                "code": "FAVORITE_REMOVED",
                "message": "즐겨찾기에서 해제되었습니다",
            }

        if not _station_exists(db, station_id=station_key):
            raise HTTPException(status_code=404, detail="충전소를 찾을 수 없습니다")

        count = _favorite_count(db, user_pk=user_pk)
        if count >= MAX_FAVORITES:
            db.commit()
            return {
                "processed": False,
                "is_favorite": False,
                "favorite_count": count,
                "code": "FAVORITE_LIMIT_REACHED",
                "message": "즐겨찾기는 최대 10개까지 등록할 수 있습니다",
            }

        now = _now()
        db.add(
            UserFavoriteStation(
                user_id=user_pk,
                stat_id=station_key,
                memo=memo_value,
                created_at=now,
                last_used_at=now,
            )
        )
        db.commit()
        return {
            "processed": True,
            "is_favorite": True,
            "favorite_count": count + 1,
            "code": "FAVORITE_ADDED",
            "message": "즐겨찾기에 등록되었습니다",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def add_favorite(
    db: Session,
    *,
    user_pk: int,
    station_id: str,
    memo: str | None,
) -> dict[str, object]:
    """
    즐겨찾기 등록.

    - 이미 등록된 경우 409.
    - 10개 제한은 HTTP 오류가 아니라 processed=false 결과로 반환한다.
    """
    station_key = _normalize_station_id(station_id)
    memo_value = (memo or "").strip() or None

    try:
        _lock_user(db, user_pk=user_pk)

        favorite = db.scalar(
            select(UserFavoriteStation).where(
                UserFavoriteStation.user_id == user_pk,
                UserFavoriteStation.stat_id == station_key,
            )
        )
        if favorite is not None:
            raise HTTPException(status_code=409, detail="이미 즐겨찾기에 등록된 충전소입니다")

        if not _station_exists(db, station_id=station_key):
            raise HTTPException(status_code=404, detail="충전소를 찾을 수 없습니다")

        count = _favorite_count(db, user_pk=user_pk)
        if count >= MAX_FAVORITES:
            db.commit()
            return {
                "processed": False,
                "is_favorite": False,
                "favorite_count": count,
                "code": "FAVORITE_LIMIT_REACHED",
                "message": "즐겨찾기는 최대 10개까지 등록할 수 있습니다",
            }

        now = _now()
        db.add(
            UserFavoriteStation(
                user_id=user_pk,
                stat_id=station_key,
                memo=memo_value,
                created_at=now,
                last_used_at=now,
            )
        )
        db.commit()
        return {
            "processed": True,
            "is_favorite": True,
            "favorite_count": count + 1,
            "code": "FAVORITE_ADDED",
            "message": "즐겨찾기에 등록되었습니다",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def update_favorite_memo(
    db: Session,
    *,
    user_pk: int,
    station_id: str,
    memo: str | None,
) -> dict[str, object]:
    """등록된 즐겨찾기 메모만 갱신. 없으면 404."""
    station_key = _normalize_station_id(station_id)
    memo_value = (memo or "").strip() or None
    if memo_value and len(memo_value) > 100:
        raise HTTPException(status_code=400, detail="memo는 100자 이하여야 합니다")

    try:
        favorite = db.scalar(
            select(UserFavoriteStation).where(
                UserFavoriteStation.user_id == user_pk,
                UserFavoriteStation.stat_id == station_key,
            )
        )
        if favorite is None:
            raise HTTPException(
                status_code=404, detail="즐겨찾기에 등록되지 않은 충전소입니다"
            )
        favorite.memo = memo_value
        db.commit()
        return {"station_id": station_key, "memo": memo_value}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def remove_favorite(
    db: Session,
    *,
    user_pk: int,
    station_id: str,
) -> dict[str, object]:
    """즐겨찾기 해제. 미등록이면 404."""
    station_key = _normalize_station_id(station_id)

    try:
        _lock_user(db, user_pk=user_pk)

        favorite = db.scalar(
            select(UserFavoriteStation).where(
                UserFavoriteStation.user_id == user_pk,
                UserFavoriteStation.stat_id == station_key,
            )
        )
        if favorite is None:
            raise HTTPException(status_code=404, detail="즐겨찾기에 등록되지 않은 충전소입니다")

        db.delete(favorite)
        db.flush()
        count = _favorite_count(db, user_pk=user_pk)
        db.commit()
        return {
            "processed": True,
            "is_favorite": False,
            "favorite_count": count,
            "code": "FAVORITE_REMOVED",
            "message": "즐겨찾기에서 해제되었습니다",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def _nullable_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)  # type: ignore[arg-type]


def _nullable_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def list_favorites(
    db: Session,
    *,
    user_pk: int,
    sort: FavoriteSort,
) -> list[dict[str, object]]:
    """
    내 즐겨찾기 충전소 전체 조회.
    ev_charger_info의 충전기별 행을 stat_id 단위로 집계한다.
    available_count는 stations와 동일: 상태 관측 없으면 null, 있으면 status=2 대수.
    """
    order_sql = (
        "COALESCE(MAX(i.stat_nm), '') ASC, f.id DESC"
        if sort == "name"
        else "f.created_at DESC, f.id DESC"
    )
    rows = db.execute(
        text(
            f"""
            SELECT
                f.id,
                f.stat_id AS station_id,
                MAX(i.stat_nm) AS name,
                MAX(i.addr) AS address,
                MAX(i.lat) AS lat,
                MAX(i.lng) AS lng,
                f.memo,
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
                f.created_at,
                f.last_used_at
            FROM user_favorite_chargers AS f
            LEFT JOIN ev_charger_info AS i
              ON i.stat_id = f.stat_id
            LEFT JOIN ev_charger_status AS s
              ON i.stat_id = s.stat_id
             AND i.chger_id = s.chger_id
            WHERE f.user_id = :user_pk
            GROUP BY
                f.id,
                f.stat_id,
                f.memo,
                f.created_at,
                f.last_used_at
            ORDER BY {order_sql}
            """
        ),
        {"user_pk": user_pk},
    ).mappings()

    return [
        {
            "id": int(row["id"]),
            "station_id": str(row["station_id"]),
            "name": row["name"],
            "address": row["address"],
            "lat": _nullable_float(row["lat"]),
            "lng": _nullable_float(row["lng"]),
            "memo": row["memo"],
            "available_count": _nullable_int(row["available_count"]),
            "created_at": row["created_at"],
            "last_used_at": row["last_used_at"],
        }
        for row in rows
    ]
