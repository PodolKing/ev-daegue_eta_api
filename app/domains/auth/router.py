# HTTP 라우팅만 담당 — 본문은 controller
from fastapi import APIRouter, Depends
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
def logout():
    return auth_controller.logout()
