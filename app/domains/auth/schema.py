from app.schemas.base import CamelModel


class AuthUserResponse(CamelModel):
    id: str
    nickname: str
    social_provider: str | None = None


class MeResponse(CamelModel):
    user: AuthUserResponse | None = None
