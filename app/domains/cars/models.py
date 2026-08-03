# cars / car_models ORM
# 관리 대상: cars | car_models는 기종 마스터(조회·등록 시 FK)
# 소프트 삭제: deleted_at 없이 is_active=False
import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, Numeric, String

from app.core.database import Base


class FuelType(str, enum.Enum):
    EV = "EV"
    PHEV = "PHEV"


class ChargingPort(str, enum.Enum):
    CCS1 = "CCS1"
    NACS = "NACS"
    CHADEMO = "CHADEMO"


class CarModel(Base):
    """차량 기종 마스터 (car_models) — CRUD 대상 아님, 등록 선택용."""

    __tablename__ = "car_models"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    manufacturer = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False)
    fuel_type = Column(
        Enum(FuelType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    charging_port = Column(
        Enum(ChargingPort, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    battery_capacity = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Car(Base):
    """사용자 차량. FK car_model_id → car_models.id."""

    __tablename__ = "cars"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 등록된 기종을 선택한 경우 car_models.id 저장
    car_model_id = Column(BigInteger, ForeignKey("car_models.id"), nullable=True)
    # 차량 번호는 선택 입력
    car_number = Column(String(20), nullable=True)
    custom_model_name = Column(String(50), nullable=True)
    # 등록 기종은 NULL 허용, 커스텀 기종은 DB CHECK에 따라 필수
    charging_port = Column(
        Enum(ChargingPort, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    is_primary = Column(Boolean, nullable=False, default=False)
    # False = 소프트 삭제 (목록에서 제외)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
