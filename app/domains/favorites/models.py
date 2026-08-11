# 충전소 단위 즐겨찾기 ORM
# 실제 user_favorite_chargers 테이블과 일치하며 DB 스키마는 변경하지 않는다.
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)

from app.core.database import Base


class UserFavoriteStation(Base):
    """사용자별 충전소 즐겨찾기. 충전기(chger_id)는 관리하지 않는다."""

    __tablename__ = "user_favorite_chargers"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "stat_id",
            name="uk_user_station",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    stat_id = Column(String(20), nullable=False)
    memo = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
    )
    last_used_at = Column(
        DateTime,
        nullable=False,
    )
