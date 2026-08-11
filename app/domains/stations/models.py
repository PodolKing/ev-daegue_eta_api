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
    """충전기 정적 명부 (getChargerInfo). 변동 상태값은 EvChargerStatus."""

    __tablename__ = "ev_charger_info"

    stat_id = Column(String(20), primary_key=True)
    chger_id = Column(String(10), primary_key=True)
    stat_nm = Column(String(100))
    chger_type = Column(String(10))
    addr = Column(String(200))
    addr_detail = Column(String(200))
    location = Column(String(200))
    lat = Column(Numeric(12, 8))
    lng = Column(Numeric(12, 8))
    use_time = Column(String(100))
    busi_id = Column(String(10))
    bnm = Column(String(100))
    busi_nm = Column(String(100))
    busi_call = Column(String(50))
    output = Column(Numeric(10, 2))
    method = Column(String(50))
    zcode = Column(String(10))
    zscode = Column(String(10))
    kind = Column(String(10))
    kind_detail = Column(String(20))
    parking_free = Column(String(5))
    note = Column(String(500))
    limit_yn = Column(String(5))
    limit_detail = Column(String(200))
    del_yn = Column(String(5))
    del_detail = Column(String(200))
    traffic_yn = Column(String(5))
    install_year = Column(String(10))
    floor_num = Column(String(10))
    floor_type = Column(String(10))
    updated_at = Column(DateTime)


class EvChargerStatus(Base):
    """충전기 현재 상태 스냅샷 (getChargerStatus). 출력 kW는 info.output."""

    __tablename__ = "ev_charger_status"

    stat_id = Column(String(20), primary_key=True)
    chger_id = Column(String(10), primary_key=True)
    charger_status = Column(String(20))
    last_updated = Column(DateTime)


class FuelType(str, enum.Enum):
    EV = "EV"
    PHEV = "PHEV"


class ChargingPort(str, enum.Enum):
    CCS1 = "CCS1"
    NACS = "NACS"
    CHADEMO = "CHADEMO"
