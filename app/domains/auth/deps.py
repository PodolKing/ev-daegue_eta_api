# JWT Bearer 인증 Depends (보편적 FastAPI 패턴)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth import service as auth_service
from app.domains.auth.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session | None = Depends(get_db),
) -> User:
    """Authorization: Bearer <JWT> → User. 실패 시 401."""
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="DB 미설정")
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="인증 필요")
        payload = auth_service.decode_access_token(credentials.credentials)
        user = auth_service.get_user_by_token_payload(db, payload)
        if user is None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없음")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="인증 실패") from None


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session | None = Depends(get_db),
) -> User | None:
    """토큰 없으면 None (GET /me용)."""
    try:
        if credentials is None or db is None:
            return None
        if credentials.scheme.lower() != "bearer":
            return None
        payload = auth_service.decode_access_token(credentials.credentials)
        return auth_service.get_user_by_token_payload(db, payload)
    except HTTPException:
        return None
    except Exception:
        return None
