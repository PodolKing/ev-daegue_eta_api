# router ↔ service: 요청 조립, 응답 스키마 변환
from fastapi import HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
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


def _set_auth_cookie(response: Response, token: str) -> None:
    """JWT를 HttpOnly 쿠키로 심기 (소셜·로컬 공통 가능)."""
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """로그아웃 시 인증 쿠키 삭제."""
    settings = get_settings()
    response.delete_cookie(key=settings.auth_cookie_name, path="/")


def signup(db: Session | None, body: SignupRequest) -> SignupResponse:
    session = _require_db(db)
    user = auth_service.signup(
        session,
        user_id=body.user_id,
        password=body.password,
        nickname=body.nickname,
        address=body.address,
        detail_address=body.detail_address,
        user_lat=body.user_lat,
        user_lng=body.user_lng,
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


def logout(response: Response) -> dict:
    """클라이언트의 Bearer 토큰 삭제 + HttpOnly 쿠키 제거."""
    _clear_auth_cookie(response)
    return {"ok": True, "message": "클라이언트의 accessToken을 삭제하세요"}


# --- 소셜 OAuth ---


def oauth_login_redirect(provider: str, return_url: str | None) -> RedirectResponse:
    """GET /{provider}/login → 제공자 authorize URL로 302."""
    url = auth_service.build_authorize_url(provider, return_url=return_url)
    return RedirectResponse(url=url, status_code=302)


def oauth_callback(
    db: Session | None,
    provider: str,
    *,
    code: str | None,
    state: str | None,
    error: str | None = None,
) -> RedirectResponse:
    """GET /{provider}/callback → upsert + 쿠키 JWT → FE 리다이렉트."""
    if error:
        return RedirectResponse(
            url=auth_service.frontend_error_redirect(error),
            status_code=302,
        )
    try:
        session = _require_db(db)
        token, _user, redirect_url = auth_service.complete_oauth_callback(
            session,
            provider=provider,
            code=code,
            state=state,
        )
        response = RedirectResponse(url=redirect_url, status_code=302)
        _set_auth_cookie(response, token)
        return response
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "oauth_failed"
        return RedirectResponse(
            url=auth_service.frontend_error_redirect(detail),
            status_code=302,
        )
