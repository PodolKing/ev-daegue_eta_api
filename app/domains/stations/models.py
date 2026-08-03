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
