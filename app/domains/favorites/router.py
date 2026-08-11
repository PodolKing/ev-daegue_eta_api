# 즐겨찾기 HTTP 라우터
# 현재 작업물에서는 app/main.py에 등록하지 않는다.
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.deps import get_current_user
from app.domains.auth.models import User

from . import controller as favorites_controller
from .schema import (
    FavoriteListResponse,
    FavoriteMutationResponse,
    FavoriteSort,
    FavoriteStatusResponse,
    FavoriteToggleRequest,
)

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


@router.get("/list", response_model=FavoriteListResponse)
def list_favorites(
    sort: FavoriteSort = Query(
        "recent",
        description="recent=최신 등록순, name=충전소명 가나다순",
    ),
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteListResponse:
    """내 즐겨찾기 충전소 전체 조회."""
    return favorites_controller.list_mine(db, user, sort)


@router.get("/status/{station_id}", response_model=FavoriteStatusResponse)
def favorite_status(
    station_id: str,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """장소 정보의 즐겨찾기 마크 상태 조회."""
    return favorites_controller.status(db, user, station_id)


@router.post("/toggle", response_model=FavoriteMutationResponse)
def toggle_favorite(
    body: FavoriteToggleRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteMutationResponse:
    """
    즐겨찾기 마크 토글.
    등록 10개 초과 시 오류 대신 processed=false를 반환한다.
    """
    return favorites_controller.toggle(db, user, body)
