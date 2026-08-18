# HTTP 라우팅만 담당 — 본문은 controller
# 내 차량 조회 / 기종 목록 / 등록 / 소프트 삭제
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.deps import get_current_user
from app.domains.auth.models import User
from app.domains.cars import controller as cars_controller
from app.domains.cars.schema import (
    CarCreateRequest,
    CarDeleteResponse,
    CarListResponse,
    CarModelsResponse,
    CarPrimaryUpdateRequest,
    CarPublic,
    CarUpdateRequest,
)

router = APIRouter(prefix="/api/v1/cars", tags=["cars"])


@router.get("/models", response_model=CarModelsResponse)
def list_car_models(
    db: Session | None = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CarModelsResponse:
    """기종 마스터 목록 (등록 화면용). /{carId}보다 먼저 선언."""
    return cars_controller.list_models(db)


@router.get("/listCar", response_model=CarListResponse)
def list_my_cars(
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CarListResponse:
    """내 활성 차량 목록 (is_active=1)."""
    return cars_controller.list_mine(db, user)


@router.post("/createCar", response_model=CarPublic)
def create_car(
    body: CarCreateRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CarPublic:
    """차량 등록 — carModelId 또는 customModelName. 커스텀은 chargingPort 필수."""
    return cars_controller.create(db, user, body)


@router.patch("/updateCar/{car_id}", response_model=CarPublic)
def update_car(
    car_id: int,
    body: CarUpdateRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CarPublic:
    """차량 번호·포트·커스텀명 수정. 기종 교체·대표는 별도."""
    return cars_controller.update(db, user, car_id, body)


@router.patch("/setPrimary/{car_id}", response_model=CarPublic)
def set_primary_car(
    car_id: int,
    body: CarPrimaryUpdateRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CarPublic:
    """대표 차량 설정 또는 해제. 대표 차량이 없어도 허용."""
    return cars_controller.set_primary(db, user, car_id, body)


@router.delete("/deleteCar/{car_id}", response_model=CarDeleteResponse)
def delete_car(
    car_id: int,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CarDeleteResponse:
    """소프트 삭제 (is_active=0). deleted_at 미사용."""
    return cars_controller.delete(db, user, car_id)
