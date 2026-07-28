# users 테이블 ORM (Express/Prisma user 테이블이 아님)
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, String

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True)  # 로그인 아이디
    password = Column(String(255), nullable=False)  # bcrypt 해시만 저장
    nickname = Column(String(30), nullable=False, unique=True)  # UNIQUE
    point = Column(Integer, nullable=False, default=0)
    role = Column(
        Enum("USER", "MANAGER", "ADMIN", name="user_role"),
        nullable=False,
        default="USER",
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # soft delete
    address = Column(String(255), nullable=True)
