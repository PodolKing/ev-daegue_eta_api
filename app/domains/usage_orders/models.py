# usage_orders / ev_operator_tariffs ORM
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import Base


class UsageOrder(Base):
    """충전 이용·요금 주문 (가결제 → 정산)."""

    __tablename__ = "usage_orders"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_usage_orders_idempotency"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    stat_id = Column(String(20), nullable=True)
    chger_id = Column(String(10), nullable=True)
    busi_id = Column(String(10), nullable=True)
    kwh = Column(Numeric(8, 2), nullable=False)
    kwh_source = Column(String(32), nullable=False)
    rate_member_won = Column(Numeric(8, 2), nullable=False)
    rate_non_member_won = Column(Numeric(8, 2), nullable=True)
    amount_list_krw = Column(Integer, nullable=False)
    amount_charge_krw = Column(Integer, nullable=False)
    discount_krw = Column(Integer, nullable=False, default=0)
    points_spent = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False)
    memo = Column(String(255), nullable=True)
    idempotency_key = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class OperatorTariff(Base):
    """사업자 회원/비회원 요금. PK=(busi_id, member_type)."""

    __tablename__ = "ev_operator_tariffs"

    busi_id = Column(String(10), primary_key=True)
    member_type = Column(String(20), primary_key=True)
    operator_nm = Column(String(100), nullable=True)
    rate_date = Column(Date, nullable=True)
    rate_slow_3_5 = Column(Numeric(8, 2), nullable=True)
    rate_slow_7 = Column(Numeric(8, 2), nullable=True)
    rate_slow_11 = Column(Numeric(8, 2), nullable=True)
    rate_mid_14 = Column(Numeric(8, 2), nullable=True)
    rate_mid_30 = Column(Numeric(8, 2), nullable=True)
    rate_fast_50 = Column(Numeric(8, 2), nullable=True)
    rate_fast_100 = Column(Numeric(8, 2), nullable=True)
    rate_ultra_200 = Column(Numeric(8, 2), nullable=True)
    rate_ultra_350 = Column(Numeric(8, 2), nullable=True)
    default_rate = Column(Numeric(8, 2), nullable=True)
    source = Column(String(80), nullable=True)
    confidence = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
