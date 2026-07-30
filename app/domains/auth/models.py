# users 테이블 ORM (Express/Prisma user 테이블이 아님)
import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, Numeric, String

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


# 소셜 로그인: 가입 경로 ENUM (local + 3사)
class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    KAKAO = "kakao"
    NAVER = "naver"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True)
    # 소셜 계정은 password NULL 허용
    password = Column(String(255), nullable=True)
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
    # email 컬럼 제거 — 소셜 식별은 provider + provider_id 사용
    # 가입 경로 (ENUM: local | google | kakao | naver)
    provider = Column(
        Enum(
            AuthProvider,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AuthProvider.LOCAL,
    )
    # 소셜 제공자 유저 ID. 로컬 계정은 NULL
    provider_id = Column(String(255), nullable=True)
