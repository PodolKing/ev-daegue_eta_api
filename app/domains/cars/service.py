# cars 비즈니스 — 내 차량 조회 / 등록 / 소프트 삭제(is_active=0)
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domains.cars.models import Car, CarModel, ChargingPort


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_port(value: str | None) -> ChargingPort | None:
    """선택 입력 charging_port ENUM 검증."""
    if value is None or not value.strip():
        return None
    key = (value or "").strip().upper()
    try:
        return ChargingPort(key)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="chargingPort는 CCS1, NACS, CHADEMO 중 하나여야 합니다",
        ) from exc


def list_car_models(db: Session) -> list[CarModel]:
    """기종 마스터 목록 (등록 UI용)."""
    return list(
        db.scalars(
            select(CarModel).order_by(CarModel.manufacturer, CarModel.model_name)
        ).all()
    )


def get_car_model(db: Session, model_id: int) -> CarModel | None:
    return db.scalar(select(CarModel).where(CarModel.id == model_id))


def list_my_cars(db: Session, *, user_pk: int) -> list[Car]:
    """내 활성 차량만 (is_active=True)."""
    return list(
        db.scalars(
            select(Car)
            .where(Car.user_id == user_pk, Car.is_active.is_(True))
            .order_by(Car.is_primary.desc(), Car.id.desc())
        ).all()
    )


def _clear_primary(db: Session, *, user_pk: int) -> None:
    """같은 유저의 기존 primary 해제."""
    db.execute(
        update(Car)
        .where(
            Car.user_id == user_pk,
            Car.is_active.is_(True),
            Car.is_primary.is_(True),
        )
        .values(is_primary=False, updated_at=_now())
    )


def create_car(
    db: Session,
    *,
    user_pk: int,
    car_model_id: int | None,
    car_number: str | None,
    custom_model_name: str | None,
    charging_port: str | None,
    is_primary: bool,
) -> Car:
    """
    차량 등록.
    - CHECK: car_model_id 또는 custom_model_name 필수
    - car_model_id 있으면 car_models 존재 확인
    - 커스텀 기종은 charging_port 필수
    - is_primary면 기존 primary 해제
    """
    try:
        custom = (custom_model_name or "").strip() or None
        number = (car_number or "").strip() or None
        if car_model_id is None and not custom:
            raise HTTPException(
                status_code=400,
                detail="carModelId 또는 customModelName 중 하나는 필수입니다",
            )
        if custom and len(custom) > 50:
            raise HTTPException(status_code=400, detail="customModelName은 50자 이하여야 합니다")
        if number and len(number) > 20:
            raise HTTPException(status_code=400, detail="carNumber는 20자 이하여야 합니다")

        if car_model_id is not None:
            model = get_car_model(db, car_model_id)
            if model is None:
                raise HTTPException(
                    status_code=400,
                    detail="존재하지 않는 기종(carModelId)",
                )

        port = _parse_port(charging_port)
        if car_model_id is None and custom and port is None:
            raise HTTPException(
                status_code=400,
                detail="커스텀 기종은 chargingPort가 필수입니다",
            )

        if is_primary:
            _clear_primary(db, user_pk=user_pk)

        now = _now()
        car = Car(
            user_id=user_pk,
            car_model_id=car_model_id,
            car_number=number,
            custom_model_name=custom,
            charging_port=port,
            is_primary=bool(is_primary),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(car)
        db.commit()
        db.refresh(car)
        return car
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def set_primary_car(
    db: Session,
    *,
    user_pk: int,
    car_id: int,
    is_primary: bool,
) -> Car:
    """
    대표 차량 설정/해제.

    - true: 기존 대표 차량을 해제하고 대상만 대표로 설정
    - false: 대상 차량의 대표 설정만 해제
    - 대표 차량이 없는 상태도 허용
    """
    try:
        # 같은 사용자의 활성 차량을 잠가 동시 설정 충돌 방지
        cars = list(
            db.scalars(
                select(Car)
                .where(
                    Car.user_id == user_pk,
                    Car.is_active.is_(True),
                )
                .order_by(Car.id)
                .with_for_update()
            ).all()
        )
        target = next((car for car in cars if int(car.id) == car_id), None)
        if target is None:
            raise HTTPException(status_code=404, detail="차량을 찾을 수 없음")

        now = _now()
        if is_primary:
            # 사용자당 대표 차량은 최대 1대
            for car in cars:
                new_value = int(car.id) == car_id
                if bool(car.is_primary) != new_value:
                    car.is_primary = new_value
                    car.updated_at = now
        else:
            # 대표 차량 설정은 필수가 아니므로 단독 해제 가능
            target.is_primary = False
            target.updated_at = now

        db.commit()
        db.refresh(target)
        return target
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def soft_delete_car(db: Session, *, user_pk: int, car_id: int) -> None:
    """소프트 삭제 — is_active=False (deleted_at 미사용). 자동 primary 승격 없음."""
    try:
        car = db.scalar(
            select(Car).where(
                Car.id == car_id,
                Car.user_id == user_pk,
                Car.is_active.is_(True),
            )
        )
        if car is None:
            raise HTTPException(status_code=404, detail="차량을 찾을 수 없음")

        car.is_active = False
        car.is_primary = False
        car.updated_at = _now()
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None
