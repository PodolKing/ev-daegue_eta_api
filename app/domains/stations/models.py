import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class EvChargerInfo(Base):
    __tablename__ = "ev_charger_info"

    stat_id = Column(String(20), primary_key=True)
    chger_id = Column(String(10), primary_key=True)
    stat_nm = Column(String(100))
    chger_type = Column(String(10))
    addr = Column(String(200))
    lat = Column(Numeric(12, 8))
    lng = Column(Numeric(12, 8))
    zcode = Column(String(10))
    zscode = Column(String(10))
    install_year = Column(String(10))
    updated_at = Column(DateTime)


class EvChargerStatus(Base):
    __tablename__ = "ev_charger_status"

    stat_id = Column(String(20), primary_key=True)
    chger_id = Column(String(10), primary_key=True)
    charger_status = Column(String(20))
    output_now = Column(Numeric(10, 2))
    last_updated = Column(DateTime)


class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(30), nullable=False)
    point = Column(Integer, nullable=False, default=0)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    address = Column(String(255), nullable=True)


class UserFavoriteCharger(Base):
    __tablename__ = "user_favorite_chargers"
    __table_args__ = (
        UniqueConstraint("user_id", "stat_id", "chger_id", name="uk_user_charger"),
        ForeignKeyConstraint(
            ["stat_id", "chger_id"],
            ["ev_charger_info.stat_id", "ev_charger_info.chger_id"],
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    stat_id = Column(String(20), nullable=False)
    chger_id = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class FuelType(str, enum.Enum):
    EV = "EV"
    PHEV = "PHEV"


class ChargingPort(str, enum.Enum):
    CCS1 = "CCS1"
    NACS = "NACS"
    CHADEMO = "CHADEMO"


class CarModel(Base):
    __tablename__ = "car_models"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    manufacturer = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False)
    fuel_type = Column(Enum(FuelType), nullable=False)
    charging_port = Column(Enum(ChargingPort), nullable=True)
    battery_capacity = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Car(Base):
    __tablename__ = "cars"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    car_model_id = Column(BigInteger, ForeignKey("car_models.id"), nullable=True)
    nickname = Column(String(30), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    custom_model_name = Column(String(50), nullable=True)
