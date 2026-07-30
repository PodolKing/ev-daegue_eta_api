# HTTP 라우팅만 담당 — 본문은 controller
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth import controller as auth_controller
from app.domains.auth.deps import get_current_user_optional
from app.domains.auth.models import User
from app.domains.auth.schema import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    SignupRequest,
    SignupResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
def signup(body: SignupRequest, db: Session | None = Depends(get_db)) -> SignupResponse:
    return auth_controller.signup(db, body)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session | None = Depends(get_db)) -> LoginResponse:
    return auth_controller.login(db, body)


@router.get("/me", response_model=MeResponse)
def me(user: User | None = Depends(get_current_user_optional)) -> MeResponse:
    return auth_controller.me(user)


@router.post("/logout")
def logout(response: Response):
    # HttpOnly 쿠키 삭제 포함
    return auth_controller.logout(response)


# --- 소셜 OAuth (google | kakao | naver) — 리다이렉트 전용 ---


@router.get("/{provider}/login", response_class=RedirectResponse)
def oauth_login(
    provider: str,
    return_url: str | None = Query(None, alias="returnUrl"),
) -> RedirectResponse:
    """소셜 로그인 시작 — 제공자 authorize로 302."""
    return auth_controller.oauth_login_redirect(provider, return_url)


@router.get("/{provider}/callback", response_class=RedirectResponse)
def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session | None = Depends(get_db),
) -> RedirectResponse:
    """소셜 콜백 — 회원 upsert + JWT 쿠키 → FE."""
    return auth_controller.oauth_callback(
        db,
        provider,
        code=code,
        state=state,
        error=error,
    )
