# point_wallets / point_transactions / payments ORM
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.core.database import Base


class PointWallet(Base):
    """유저당 1개 잔액 캐시. PK = users.id."""

    __tablename__ = "point_wallets"

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        primary_key=True,
    )
    balance = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class PointTransaction(Base):
    """포인트 원장. 충전 성공 시 type=charge, ref_type=payment."""

    __tablename__ = "point_transactions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uk_point_tx_idem"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    wallet_id = Column(
        BigInteger,
        ForeignKey("point_wallets.user_id"),
        nullable=False,
    )
    type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    ref_type = Column(String(30), nullable=True)
    ref_id = Column(BigInteger, nullable=True)
    idempotency_key = Column(String(100), nullable=True)
    memo = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)


class Payment(Base):
    """포인트 충전 주문(실결제). PortOne paymentId = idempotency_key."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uk_payments_idem"),
        UniqueConstraint("pg_provider", "pg_tid", name="uk_payments_pg_tid"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    amount_krw = Column(Integer, nullable=False)
    points_granted = Column(Integer, nullable=False)
    bonus_points = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False)
    pg_provider = Column(String(20), nullable=True)
    pg_tid = Column(String(100), nullable=True)
    idempotency_key = Column(String(64), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
