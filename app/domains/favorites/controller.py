# router ↔ service 요청 조립 및 응답 스키마 변환
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.models import User

from . import service as favorites_service
from .schema import (
    FavoriteItem,
    FavoriteListResponse,
    FavoriteMutationResponse,
    FavoriteSort,
    FavoriteStatusResponse,
    FavoriteToggleRequest,
)


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="DB 미설정")
    return db


def list_mine(
    db: Session | None,
    user: User,
    sort: FavoriteSort,
) -> FavoriteListResponse:
    """로그인 사용자의 즐겨찾기 전체 조회."""
    session = _require_db(db)
    rows = favorites_service.list_favorites(
        session,
        user_pk=int(user.id),
        sort=sort,
    )
    items = [FavoriteItem.model_validate(row) for row in rows]
    return FavoriteListResponse(items=items, count=len(items))


def status(
    db: Session | None,
    user: User,
    station_id: str,
) -> FavoriteStatusResponse:
    """특정 충전소의 즐겨찾기 여부."""
    session = _require_db(db)
    result = favorites_service.is_favorite(
        session,
        user_pk=int(user.id),
        station_id=station_id,
    )
    return FavoriteStatusResponse(
        station_id=station_id,
        is_favorite=result,
    )


def toggle(
    db: Session | None,
    user: User,
    body: FavoriteToggleRequest,
) -> FavoriteMutationResponse:
    """즐겨찾기 등록/해제 토글."""
    session = _require_db(db)
    result = favorites_service.toggle_favorite(
        session,
        user_pk=int(user.id),
        station_id=body.station_id,
        memo=body.memo,
    )
    return FavoriteMutationResponse.model_validate(result)
