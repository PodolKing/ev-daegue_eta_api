from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.domains.auth import service as auth_service
from app.domains.auth.schema import AuthUserResponse, MeResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# 1주차 provider: kakao (확정 시 path 세그먼트와 맞춤)
SUPPORTED_PROVIDERS = {"kakao"}


@router.get("/me", response_model=MeResponse)
def me() -> MeResponse:
    """Current session user. TODO: wire session/JWT."""
    user = auth_service.get_current_user_from_session()
    if user is None:
        return MeResponse(user=None)
    return MeResponse(user=AuthUserResponse.model_validate(user))


@router.post("/logout")
def logout():
    """Clear session cookie. TODO: implement."""
    raise HTTPException(status_code=501, detail="auth /logout not implemented")


@router.get("/{provider}/login")
def login_start(
    provider: str,
    return_url: str | None = Query(None, alias="returnUrl"),
):
    """
    Start OAuth redirect flow (no popup).
    TODO: RedirectResponse to provider authorize URL after validate_return_url.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="unsupported provider")
    safe = auth_service.validate_return_url(return_url)
    try:
        url = auth_service.build_provider_authorize_url(provider, safe)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=f"auth /{provider}/login not implemented",
        ) from None
    return RedirectResponse(url)


@router.get("/{provider}/callback")
def oauth_callback(
    provider: str,
    code: str | None = Query(None),
    state: str | None = Query(None),
    return_url: str | None = Query(None, alias="returnUrl"),
):
    """
    OAuth provider callback → issue session/JWT cookie → redirect to returnUrl.
    TODO: exchange code, set cookie, RedirectResponse(validate_return_url(...)).
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="unsupported provider")
    safe = auth_service.validate_return_url(return_url)
    _ = (code, state)
    # TODO: exchange_code_for_session + Set-Cookie + redirect
    raise HTTPException(
        status_code=501,
        detail=f"auth /{provider}/callback not implemented (would redirect to {safe})",
    )
