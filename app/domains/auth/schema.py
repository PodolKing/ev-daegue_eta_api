from datetime import datetime

from pydantic import Field

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


class UpdateProfileRequest(CamelModel):
    """회원 정보 수정 — 닉네임·주소(상세 포함). 보낸 필드만 갱신."""

    nickname: str | None = Field(default=None, min_length=1, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    detail_address: str | None = Field(default=None, max_length=255)


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


class KakaoNativeLoginRequest(CamelModel):
    """Flutter Kakao SDK access token → our JWT."""

    access_token: str = Field(..., min_length=8)


class NaverNativeLoginRequest(CamelModel):
    """Flutter Naver SDK access token → our JWT."""

    access_token: str = Field(..., min_length=8)


class UpdateProfileResponse(CamelModel):
    success: bool = True
    message: str = "회원 정보가 수정되었습니다"
    user: UserPublic


class WithdrawResponse(CamelModel):
    success: bool = True
    message: str = "회원 탈퇴가 완료되었습니다"
