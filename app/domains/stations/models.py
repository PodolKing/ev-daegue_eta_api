from sqlalchemy import Column, DateTime, Numeric, String

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
