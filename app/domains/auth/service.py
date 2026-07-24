DEFAULT_RETURN_PATH = "/map"


def validate_return_url(return_url: str | None) -> str:
    """
    Allow only internal relative paths starting with `/map` (open-redirect guard).
    TODO: reject `//evil`, backslash tricks, encoded schemes; align with FE sanitizeReturnUrl.
    """
    if not return_url:
        return DEFAULT_RETURN_PATH
    trimmed = return_url.strip()
    if not trimmed.startswith(DEFAULT_RETURN_PATH):
        return DEFAULT_RETURN_PATH
    if trimmed.startswith("//"):
        return DEFAULT_RETURN_PATH
    # TODO: additional hardening
    return trimmed


def build_provider_authorize_url(provider: str, return_url: str) -> str:
    """
    TODO: build OAuth authorize URL (kakao etc.) with state carrying validated return_url.
    """
    _ = (provider, return_url)
    raise NotImplementedError("auth: build_provider_authorize_url")


def exchange_code_for_session(provider: str, code: str) -> dict:
    """
    TODO: token exchange with provider, upsert user, issue JWT/session cookie payload.
    """
    _ = (provider, code)
    raise NotImplementedError("auth: exchange_code_for_session")


def get_current_user_from_session() -> dict | None:
    """TODO: read cookie/JWT and load user."""
    return None
