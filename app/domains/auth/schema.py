from datetime import datetime

from app.schemas.base import CamelModel


# --- 로컬 계정 (id/pw) — nick → nickname, id → user_id, pw → password ---


class SignupRequest(CamelModel):
    user_id: str
    password: str
    nickname: str
    address: str | None = None
    detail_address: str | None = None
    user_lat: float | None = None
    user_lng: float | None = None
    # email 필드 제거 (소셜은 provider/provider_id로 식별)


class LoginRequest(CamelModel):
    user_id: str
    password: str


class UserPublic(CamelModel):
    """공개 유저 응답 — password 절대 포함하지 않음. /me·login·signup 공통."""

    id: int
    user_id: str
    nickname: str
    point: int
    role: str
    is_active: bool
    address: str | None = None
    detail_address: str | None = None
    created_at: datetime
    updated_at: datetime
    # 가입 경로: local | google | kakao | naver
    provider: str = "local"
    user_lat: float | None = None
    user_lng: float | None = None


class MeResponse(CamelModel):
    user: UserPublic | None = None


class SignupResponse(CamelModel):
    success: bool = True
    message: str = "회원 가입 성공"
    user: UserPublic


class LoginResponse(CamelModel):
    success: bool = True
    message: str = "로그인 성공"
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
