# JWT Bearer + HttpOnly 쿠키 인증 Depends
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.auth import service as auth_service
from app.domains.auth.models import User

_bearer = HTTPBearer(auto_error=False)


def _token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Authorization Bearer 우선, 없으면 auth 쿠키."""
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    # 소셜 로그인 후 HttpOnly 쿠키
    settings = get_settings()
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session | None = Depends(get_db),
) -> User:
    """Bearer 또는 쿠키 JWT → User. 실패 시 401."""
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="DB 미설정")
        token = _token_from_request(request, credentials)
        if not token:
            raise HTTPException(status_code=401, detail="인증 필요")
        payload = auth_service.decode_access_token(token)
        user = auth_service.get_user_by_token_payload(db, payload)
        if user is None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없음")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="인증 실패") from None


def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session | None = Depends(get_db),
) -> User | None:
    """토큰 없으면 None (GET /me용). Bearer 또는 쿠키."""
    try:
        if db is None:
            return None
        token = _token_from_request(request, credentials)
        if not token:
            return None
        payload = auth_service.decode_access_token(token)
        return auth_service.get_user_by_token_payload(db, payload)
    except HTTPException:
        return None
    except Exception:
        return None
