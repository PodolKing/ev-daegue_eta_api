# router ↔ service: 요청 조립, 응답 스키마 변환
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.models import User
from app.domains.cars import service as cars_service
from app.domains.cars.models import Car, CarModel
from app.domains.cars.schema import (
    CarCreateRequest,
    CarDeleteResponse,
    CarListResponse,
    CarModelPublic,
    CarModelsResponse,
    CarPrimaryUpdateRequest,
    CarPublic,
)


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="DB 미설정")
    return db


def _model_public(model: CarModel | None) -> CarModelPublic | None:
    """기종 ORM → 공개 스키마. 없으면 null (FE「정보 없음」)."""
    if model is None:
        return None
    return CarModelPublic.model_validate(model)


def _car_public(db: Session, car: Car) -> CarPublic:
    """차량 + 기종 조인 요약."""
    model = None
    if car.car_model_id is not None:
        model = cars_service.get_car_model(db, int(car.car_model_id))
    return CarPublic(
        id=int(car.id),
        car_model_id=(
            int(car.car_model_id) if car.car_model_id is not None else None
        ),
        car_number=car.car_number,
        custom_model_name=car.custom_model_name,
        charging_port=(
            car.charging_port.value
            if hasattr(car.charging_port, "value")
            else str(car.charging_port) if car.charging_port is not None else None
        ),
        is_primary=bool(car.is_primary),
        created_at=car.created_at,
        updated_at=car.updated_at,
        model=_model_public(model),
    )


def list_models(db: Session | None) -> CarModelsResponse:
    """기종 목록."""
    session = _require_db(db)
    rows = cars_service.list_car_models(session)
    items = [CarModelPublic.model_validate(row) for row in rows]
    return CarModelsResponse(items=items, count=len(items))


def list_mine(db: Session | None, user: User) -> CarListResponse:
    """내 활성 차량 목록."""
    session = _require_db(db)
    rows = cars_service.list_my_cars(session, user_pk=int(user.id))
    items = [_car_public(session, row) for row in rows]
    return CarListResponse(items=items, count=len(items))


def create(db: Session | None, user: User, body: CarCreateRequest) -> CarPublic:
    """차량 등록."""
    session = _require_db(db)
    car = cars_service.create_car(
        session,
        user_pk=int(user.id),
        car_model_id=body.car_model_id,
        car_number=body.car_number,
        custom_model_name=body.custom_model_name,
        charging_port=body.charging_port,
        is_primary=body.is_primary,
    )
    return _car_public(session, car)


def set_primary(
    db: Session | None,
    user: User,
    car_id: int,
    body: CarPrimaryUpdateRequest,
) -> CarPublic:
    """내 차량의 대표 설정을 변경."""
    session = _require_db(db)
    car = cars_service.set_primary_car(
        session,
        user_pk=int(user.id),
        car_id=car_id,
        is_primary=body.is_primary,
    )
    return _car_public(session, car)


def delete(db: Session | None, user: User, car_id: int) -> CarDeleteResponse:
    """소프트 삭제."""
    session = _require_db(db)
    cars_service.soft_delete_car(session, user_pk=int(user.id), car_id=car_id)
    return CarDeleteResponse()
