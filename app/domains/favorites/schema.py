# favorites API 요청·응답 스키마 (CamelModel → JSON camelCase)
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel


class FavoriteToggleRequest(CamelModel):
    """별 마크 클릭 시 등록/해제할 충전소."""

    station_id: str = Field(min_length=1, max_length=20)
    memo: str | None = Field(default=None, max_length=100)


class FavoriteMutationResponse(CamelModel):
    """토글 결과. 10개 제한은 오류 대신 processed=false로 반환한다."""

    processed: bool
    is_favorite: bool
    favorite_count: int
    code: str
    message: str


class FavoriteStatusResponse(CamelModel):
    """특정 충전소의 현재 즐겨찾기 상태."""

    station_id: str
    is_favorite: bool


class FavoriteItem(CamelModel):
    """즐겨찾기 목록의 충전소 요약."""

    id: int
    station_id: str
    name: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    memo: str | None = None
    available_count: int | None = Field(
        default=None,
        description="관측 없으면 null(0과 구분). charger_status=2 대수. stations와 동일.",
    )
    created_at: datetime
    last_used_at: datetime


class FavoriteListResponse(CamelModel):
    items: list[FavoriteItem]
    count: int


FavoriteSort = Literal["recent", "name"]
