# FastAPI + SQLAlchemy + JWT 로컬/소셜 계정
# 소셜: Authlib(OAuth2) + itsdangerous(state) + HttpOnly 쿠키 JWT

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode, urlparse

import bcrypt
import httpx
import jwt
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.httpx_client import OAuth2Client
from fastapi import HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.auth.models import AuthProvider, User, UserRole

# 소셜 제공자만 (로컬은 /signup·/login)
SOCIAL_PROVIDERS = frozenset(
    {AuthProvider.GOOGLE.value, AuthProvider.KAKAO.value, AuthProvider.NAVER.value}
)

# OAuth 엔드포인트 메타
_OAUTH_META: dict[str, dict[str, str]] = {
    AuthProvider.GOOGLE.value: {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
    AuthProvider.KAKAO.value: {
        "authorize": "https://kauth.kakao.com/oauth/authorize",
        "token": "https://kauth.kakao.com/oauth/token",
        "userinfo": "https://kapi.kakao.com/v2/user/me",
        # 닉네임은 서버에서 카카오+번호로 생성 — profile_nickname 동의 불필요
        "scope": "",
    },
    AuthProvider.NAVER.value: {
        "authorize": "https://nid.naver.com/oauth2.0/authorize",
        "token": "https://nid.naver.com/oauth2.0/token",
        "userinfo": "https://openapi.naver.com/v1/nid/me",
        "scope": "",
    },
}


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
    detail_address: str | None,
    user_lat: float | None,
    user_lng: float | None,
) -> User:
    """로컬 회원가입 — provider=local, provider_id=NULL."""
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
            detail_address=detail_address,
            user_lat=user_lat,
            user_lng=user_lng,
            # 로컬 가입 경로
            provider=AuthProvider.LOCAL,
            provider_id=None,
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

        # 소셜 전용 계정(password NULL)은 로컬 로그인 불가
        if user.password is None:
            raise HTTPException(
                status_code=400,
                detail="소셜 로그인 계정입니다. 소셜 로그인을 이용해주세요",
            )

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


def update_profile(
    db: Session,
    *,
    user: User,
    nickname: str | None,
    address: str | None,
    detail_address: str | None,
    address_set: bool,
    detail_address_set: bool,
) -> User:
    """닉네임·주소 수정. None이 아닌(또는 명시된) 필드만 반영."""
    try:
        if nickname is None and not address_set and not detail_address_set:
            raise HTTPException(status_code=400, detail="수정할 항목이 없습니다")

        row = db.get(User, int(user.id))
        if row is None or row.deleted_at is not None or not row.is_active:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        if nickname is not None:
            nick = nickname.strip()
            if not nick:
                raise HTTPException(status_code=400, detail="nickname은 비울 수 없습니다")
            if len(nick) > 30:
                raise HTTPException(status_code=400, detail="nickname은 30자 이내입니다")
            clash = db.scalar(
                select(User).where(
                    User.nickname == nick,
                    User.id != row.id,
                    User.deleted_at.is_(None),
                )
            )
            if clash is not None:
                raise HTTPException(status_code=400, detail="이미 사용 중인 nickname입니다")
            row.nickname = nick

        if address_set:
            if address is None:
                row.address = None
            else:
                row.address = address.strip() or None

        if detail_address_set:
            if detail_address is None:
                row.detail_address = None
            else:
                row.detail_address = detail_address.strip() or None

        row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(row)
        return row
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="nickname 중복") from None
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def withdraw_user(db: Session, *, user: User) -> None:
    """
    회원 탈퇴(소프트 삭제).
    deleted_at + is_active=False, 식별자 익명화로 UNIQUE 재가입 허용.
    """
    try:
        row = db.get(User, int(user.id))
        if row is None or row.deleted_at is not None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        pk = int(row.id)
        # VARCHAR 한도: user_id 50, nickname 30
        row.user_id = f"deleted_{pk}"[:50]
        row.nickname = f"탈퇴_{pk}"[:30]
        row.password = None
        row.provider_id = None
        row.is_active = False
        row.deleted_at = now
        row.updated_at = now
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="회원 탈퇴 처리 실패") from None
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


# --- 소셜 OAuth 헬퍼 ---


def _parse_provider(provider: str) -> AuthProvider:
    key = (provider or "").strip().lower()
    if key not in SOCIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail="지원하지 않는 소셜 제공자")
    return AuthProvider(key)


def _oauth_credentials(provider: AuthProvider) -> tuple[str, str, str]:
    """provider별 client_id / secret / redirect_uri."""
    settings = get_settings()
    mapping = {
        AuthProvider.GOOGLE: (
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_redirect_uri,
        ),
        AuthProvider.KAKAO: (
            settings.kakao_client_id,
            settings.kakao_client_secret,
            settings.kakao_redirect_uri,
        ),
        AuthProvider.NAVER: (
            settings.naver_client_id,
            settings.naver_client_secret,
            settings.naver_redirect_uri,
        ),
    }
    client_id, client_secret, redirect_uri = mapping[provider]
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail=f"{provider.value.upper()} OAuth 환경변수 미설정",
        )
    return client_id, client_secret, redirect_uri


def validate_return_url(return_url: str | None) -> str:
    """open-redirect 방지 — 상대경로 또는 허용 origin만."""
    settings = get_settings()
    default = "/map"
    if not return_url:
        return default
    raw = return_url.strip()
    # 상대 경로만 허용 (//evil.com 차단)
    if raw.startswith("/") and not raw.startswith("//"):
        return raw
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        allowed = {urlparse(o).netloc for o in settings.cors_origin_list}
        fe = urlparse(settings.frontend_origin)
        if fe.netloc:
            allowed.add(fe.netloc)
        if parsed.netloc in allowed:
            return parsed.path or default
    return default


def create_oauth_state(*, return_url: str, provider: str) -> str:
    """itsdangerous로 state 서명 (returnUrl + nonce)."""
    settings = get_settings()
    secret = settings.oauth_state_secret or settings.jwt_secret
    if not secret:
        raise HTTPException(status_code=500, detail="OAUTH_STATE_SECRET 미설정")
    serializer = URLSafeTimedSerializer(secret, salt="oauth-state")
    return serializer.dumps(
        {
            "return_url": return_url,
            "provider": provider,
            "nonce": secrets.token_urlsafe(16),
        }
    )


def parse_oauth_state(state: str, *, max_age: int = 600) -> dict[str, Any]:
    """서명된 state 검증·복원 (기본 10분)."""
    settings = get_settings()
    secret = settings.oauth_state_secret or settings.jwt_secret
    if not secret:
        raise HTTPException(status_code=500, detail="OAUTH_STATE_SECRET 미설정")
    serializer = URLSafeTimedSerializer(secret, salt="oauth-state")
    try:
        data = serializer.loads(state, max_age=max_age)
    except SignatureExpired as exc:
        raise HTTPException(status_code=400, detail="OAuth state 만료") from exc
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="OAuth state 위조") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="OAuth state 형식 오류")
    return data


def build_authorize_url(provider: str, *, return_url: str | None = None) -> str:
    """Authlib로 제공자 로그인 URL 생성."""
    auth_provider = _parse_provider(provider)
    client_id, client_secret, redirect_uri = _oauth_credentials(auth_provider)
    meta = _OAUTH_META[auth_provider.value]
    safe_return = validate_return_url(return_url)
    state = create_oauth_state(return_url=safe_return, provider=auth_provider.value)

    client = OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=meta["scope"] or None,
    )
    # Authlib create_authorization_url — state는 우리가 서명한 값 사용
    uri, _ = client.create_authorization_url(
        meta["authorize"],
        state=state,
        redirect_uri=redirect_uri,
    )
    return uri


def exchange_code_for_token(provider: AuthProvider, *, code: str) -> dict[str, Any]:
    """authorization code → access_token (Authlib OAuth2Client).

    카카오 등은 form body에 client_id/secret을 기대하므로 client_secret_post 사용.
    (기본 client_secret_basic이면 카카오가 client_id=null로 거절)
    """
    client_id, client_secret, redirect_uri = _oauth_credentials(provider)
    meta = _OAUTH_META[provider.value]
    try:
        with OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_endpoint_auth_method="client_secret_post",
        ) as client:
            token = client.fetch_token(
                meta["token"],
                code=code,
                grant_type="authorization_code",
            )
    except OAuthError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"토큰 교환 실패 ({provider.value})",
        ) from exc
    if not token or not token.get("access_token"):
        raise HTTPException(status_code=400, detail="토큰 교환 실패")
    return dict(token)


def fetch_social_profile(
    provider: AuthProvider, *, access_token: str
) -> tuple[str, str]:
    """제공자 userinfo → (provider_id, nickname)."""
    meta = _OAUTH_META[provider.value]
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(meta["userinfo"], headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=400, detail="소셜 프로필 조회 실패")
    data = resp.json()

    if provider == AuthProvider.GOOGLE:
        provider_id = str(data.get("sub") or "")
    elif provider == AuthProvider.KAKAO:
        provider_id = str(data.get("id") or "")
    else:  # NAVER
        body = data.get("response") or {}
        provider_id = str(body.get("id") or "")

    if not provider_id:
        raise HTTPException(status_code=400, detail="소셜 사용자 ID 없음")
    # UI 닉네임: 제공자 한글명 + 4자리 (프로필명·식별값 미사용)
    nickname = _social_display_nickname(provider)
    return provider_id, nickname


_SOCIAL_NICK_LABEL: dict[AuthProvider, str] = {
    AuthProvider.GOOGLE: "구글",
    AuthProvider.KAKAO: "카카오",
    AuthProvider.NAVER: "네이버",
}


def _social_display_nickname(provider: AuthProvider) -> str:
    """소셜 UI 닉네임: 구글/카카오/네이버 + 4자리 (예: 카카오4821)."""
    label = _SOCIAL_NICK_LABEL[provider]
    return f"{label}{secrets.randbelow(9000) + 1000}"


def _is_social_display_nickname(provider: AuthProvider, nickname: str | None) -> bool:
    """이미 새 형식(카카오1234 또는 충돌 접미사 포함)인지."""
    t = (nickname or "").strip()
    label = _SOCIAL_NICK_LABEL.get(provider)
    if not label or not t.startswith(label):
        return False
    rest = t[len(label) :]
    if rest.isdigit() and len(rest) == 4:
        return True
    # _unique_nickname 충돌 접미사: 카카오1234_ab12
    if "_" in rest:
        num, _, suffix = rest.partition("_")
        return num.isdigit() and len(num) == 4 and bool(suffix)
    return False


def _unique_nickname(db: Session, base: str) -> str:
    """nickname 충돌 시 접미사 부여."""
    candidate = base[:30]
    if not db.scalar(
        select(User).where(User.nickname == candidate, User.deleted_at.is_(None))
    ):
        return candidate
    for _ in range(20):
        suffix = secrets.token_hex(2)
        trimmed = f"{base[: max(1, 30 - len(suffix) - 1)]}_{suffix}"
        if not db.scalar(
            select(User).where(User.nickname == trimmed, User.deleted_at.is_(None))
        ):
            return trimmed
    raise HTTPException(status_code=500, detail="nickname 생성 실패")


def upsert_social_user(
    db: Session,
    *,
    provider: AuthProvider,
    provider_id: str,
    nickname: str,
) -> User:
    """(provider, provider_id)로 조회, 없으면 소셜 회원가입."""
    try:
        existing = db.scalar(
            select(User).where(
                User.provider == provider,
                User.provider_id == provider_id,
                User.deleted_at.is_(None),
            )
        )
        if existing:
            if not existing.is_active:
                raise HTTPException(status_code=403, detail="비활성 계정")
            # 구 프로필/식별 닉네임 → 제공자한글+번호로 1회 교체
            if not _is_social_display_nickname(provider, existing.nickname):
                existing.nickname = _unique_nickname(
                    db, _social_display_nickname(provider)
                )
                existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()
                db.refresh(existing)
            return existing

        # user_id: provider_providerId (50자 제한)
        raw_uid = f"{provider.value}_{provider_id}"
        user_id = raw_uid[:50]
        clash = db.scalar(
            select(User).where(User.user_id == user_id, User.deleted_at.is_(None))
        )
        if clash:
            user_id = f"{provider.value}_{secrets.token_hex(8)}"[:50]

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user = User(
            user_id=user_id,
            password=None,  # 소셜 계정은 비밀번호 없음
            nickname=_unique_nickname(db, nickname),
            point=0,
            role=UserRole.USER,
            is_active=True,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            provider=provider,
            provider_id=provider_id,
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
        raise HTTPException(status_code=400, detail="소셜 계정 등록 충돌") from None
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def complete_oauth_callback(
    db: Session,
    *,
    provider: str,
    code: str | None,
    state: str | None,
) -> tuple[str, User, str]:
    """
    callback 처리.
    반환: (access_token, user, frontend_redirect_url)
    """
    if not code or not state:
        raise HTTPException(status_code=400, detail="code/state 누락")

    auth_provider = _parse_provider(provider)
    state_data = parse_oauth_state(state)
    if state_data.get("provider") != auth_provider.value:
        raise HTTPException(status_code=400, detail="provider와 state 불일치")

    token = exchange_code_for_token(auth_provider, code=code)
    provider_id, nickname = fetch_social_profile(
        auth_provider, access_token=str(token["access_token"])
    )
    user = upsert_social_user(
        db,
        provider=auth_provider,
        provider_id=provider_id,
        nickname=nickname,
    )
    access_token = create_access_token(sub=str(user.user_id), user_pk=int(user.id))

    settings = get_settings()
    return_path = validate_return_url(state_data.get("return_url"))
    # FE로 리다이렉트. 토큰은 hash fragment — Vercel↔API 크로스 오리진에서도
    # localStorage Bearer로 이어짐 (쿠키만으로는 도메인이 달라 FE /me가 안 됨).
    # Supabase Auth 아님: JWT는 우리 FastAPI 발급 (DB만 Supabase/AWS 교체 가능).
    base = settings.frontend_origin.rstrip("/") + return_path
    redirect_url = f"{base}#accessToken={quote(access_token, safe='')}"
    return access_token, user, redirect_url


def frontend_error_redirect(message: str) -> str:
    """OAuth 실패 시 FE 로그인 경로로 안내."""
    settings = get_settings()
    q = urlencode({"oauthError": message})
    return f"{settings.frontend_origin.rstrip('/')}/login?{q}"
