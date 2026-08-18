# 즐겨찾기 HTTP 라우터
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.deps import get_current_user
from app.domains.auth.models import User

from . import controller as favorites_controller
from .schema import (
    FavoriteAddRequest,
    FavoriteListResponse,
    FavoriteMemoResponse,
    FavoriteMemoUpdateRequest,
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
    즐겨찾기 마크 토글 (있으면 해제, 없으면 등록).
    등록 10개 초과 시 오류 대신 processed=false를 반환한다.
    """
    return favorites_controller.toggle(db, user, body)


@router.patch("/{station_id}", response_model=FavoriteMemoResponse)
def update_favorite_memo(
    station_id: str,
    body: FavoriteMemoUpdateRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteMemoResponse:
    """즐겨찾기 메모만 수정. 등록/해제는 toggle."""
    return favorites_controller.update_memo(db, user, station_id, body)


@router.post("", response_model=FavoriteMutationResponse)
def add_favorite(
    body: FavoriteAddRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteMutationResponse:
    """
    즐겨찾기 등록.
    등록 10개 초과 시 오류 대신 processed=false를 반환한다.
    """
    return favorites_controller.add(db, user, body)


@router.delete("/{station_id}", response_model=FavoriteMutationResponse)
def remove_favorite(
    station_id: str,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FavoriteMutationResponse:
    """즐겨찾기 해제."""
    return favorites_controller.remove(db, user, station_id)
