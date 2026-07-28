# router ↔ service: 요청 조립, 응답 스키마 변환
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.auth import service as auth_service
from app.domains.auth.models import User
from app.domains.auth.schema import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    SignupRequest,
    SignupResponse,
    UserPublic,
)


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="DB 미설정")
    return db


def _to_public(user: User) -> UserPublic:
    """ORM → 공개 스키마 (password 제외)."""
    return UserPublic.model_validate(user)


def signup(db: Session | None, body: SignupRequest) -> SignupResponse:
    session = _require_db(db)
    user = auth_service.signup(
        session,
        user_id=body.user_id,
        password=body.password,
        nickname=body.nickname,
        address=body.address,
    )
    return SignupResponse(user=_to_public(user))


def login(db: Session | None, body: LoginRequest) -> LoginResponse:
    session = _require_db(db)
    token, user = auth_service.login(
        session,
        user_id=body.user_id,
        password=body.password,
    )
    return LoginResponse(
        access_token=token,
        user=_to_public(user),
    )


def me(user: User | None) -> MeResponse:
    """현재 JWT 사용자. 토큰 없으면 user=null."""
    if user is None:
        return MeResponse(user=None)
    return MeResponse(user=_to_public(user))


def logout() -> dict:
    """JWT는 서버 세션이 아님 — 클라이언트 토큰 삭제 안내."""
    return {"ok": True, "message": "클라이언트의 accessToken을 삭제하세요"}
