# users 테이블 ORM (Express/Prisma user 테이블이 아님)
import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, Numeric, String

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(30), nullable=False, unique=True)
    point = Column(Integer, nullable=False, default=0)
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    address = Column(String(255), nullable=True)
    detail_address = Column(String(255), nullable=True)
    user_lat = Column(Numeric(10, 8), nullable=True)
    user_lng = Column(Numeric(11, 8), nullable=True)
    email = Column(String(255), nullable=True)
