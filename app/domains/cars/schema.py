# cars API 스키마 (camelCase)
from datetime import datetime

from app.schemas.base import CamelModel


class CarModelPublic(CamelModel):
    """기종 공개 정보 — null 필드는 FE에서「정보 없음」."""

    id: int
    manufacturer: str
    model_name: str
    fuel_type: str
    charging_port: str | None = None
    battery_capacity: float | None = None


class CarCreateRequest(CamelModel):
    """
    차량 등록.
    DB CHECK: car_model_id 또는 custom_model_name 중 하나 이상 필수.
    커스텀 기종이면 charging_port 필수.
    """

    car_model_id: int | None = None
    car_number: str | None = None
    custom_model_name: str | None = None
    charging_port: str | None = None
    is_primary: bool = False


class CarPrimaryUpdateRequest(CamelModel):
    """대표 차량 설정(true) 또는 해제(false)."""

    is_primary: bool


class CarPublic(CamelModel):
    """내 차량 응답 (활성만). model은 기종 조인 결과, 없으면 null."""

    id: int
    car_model_id: int | None = None
    car_number: str | None = None
    custom_model_name: str | None = None
    charging_port: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    model: CarModelPublic | None = None


class CarListResponse(CamelModel):
    items: list[CarPublic]
    count: int


class CarModelsResponse(CamelModel):
    items: list[CarModelPublic]
    count: int


class CarDeleteResponse(CamelModel):
    ok: bool = True
    message: str = "차량이 삭제되었습니다"
