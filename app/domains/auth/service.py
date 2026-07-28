# FastAPI + SQLAlchemy + JWT 로컬 계정 (카카오 OAuth는 나중에 별도 추가)

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.auth.models import User, UserRole


def hash_password(plain: str) -> str:
    """bcrypt 해시."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """bcrypt 비교."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(*, sub: str, user_pk: int) -> str:
    """JWT 발급 — sub=user_id, uid=PK."""
    settings = get_settings()
    if not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET 미설정")
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": sub,
        "uid": user_pk,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """JWT 검증 후 payload 반환."""
    settings = get_settings()
    if not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET 미설정")
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 만료") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰") from None


def signup(
    db: Session,
    *,
    user_id: str,
    password: str,
    nickname: str,
    address: str | None,
) -> User:
    """회원가입 — 중복 체크 + password 해시 저장."""
    try:
        user_id = user_id.strip()
        nickname = nickname.strip()
        if not user_id or not password or not nickname:
            raise HTTPException(
                status_code=400,
                detail="userId, password, nickname 필수 입력",
            )

        existing_id = db.scalar(
            select(User).where(User.user_id == user_id, User.deleted_at.is_(None))
        )
        if existing_id:
            raise HTTPException(status_code=400, detail="이미 가입된 userId 존재")

        existing_nick = db.scalar(
            select(User).where(User.nickname == nickname, User.deleted_at.is_(None))
        )
        if existing_nick:
            raise HTTPException(status_code=400, detail="이미 가입된 nickname 존재")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user = User(
            user_id=user_id,
            password=hash_password(password),
            nickname=nickname,
            point=0,
            role=UserRole.USER,
            is_active=True,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            address=address,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="userId 또는 nickname 중복") from None
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def login(db: Session, *, user_id: str, password: str) -> tuple[str, User]:
    """로그인 — 조회 + 비번 확인 + JWT 발급."""
    try:
        user_id = user_id.strip()
        if not user_id or not password:
            raise HTTPException(
                status_code=400,
                detail="userId와 password를 입력해주세요",
            )

        user = db.scalar(
            select(User).where(User.user_id == user_id, User.deleted_at.is_(None))
        )
        if not user:
            raise HTTPException(status_code=400, detail="id 또는 password 오류")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="비활성 계정")

        if not verify_password(password, str(user.password)):
            raise HTTPException(status_code=400, detail="id 또는 password 오류")

        token = create_access_token(sub=str(user.user_id), user_pk=int(user.id))
        return token, user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def get_user_by_token_payload(db: Session, payload: dict) -> User | None:
    """JWT payload → users 행 조회."""
    try:
        uid = payload.get("uid")
        sub = payload.get("sub")
        if uid is None and not sub:
            return None
        stmt = select(User).where(User.deleted_at.is_(None))
        if uid is not None:
            stmt = stmt.where(User.id == int(uid))
        else:
            stmt = stmt.where(User.user_id == str(sub))
        user = db.scalar(stmt)
        if user is None or not user.is_active:
            return None
        return user
    except Exception:
        return None
