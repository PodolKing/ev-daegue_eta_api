from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

DbBackend = Literal["local", "supabase"]


def normalize_sqlalchemy_url(url: str) -> str:
    """Supabase dashboard URI → SQLAlchemy driver URL (IPv4 Session pooler when needed)."""
    raw = url.strip()
    if raw.startswith("postgresql+psycopg2://"):
        body = raw.removeprefix("postgresql+psycopg2://")
        prefix = "postgresql+psycopg2://"
    elif raw.startswith("postgresql://"):
        body = raw.removeprefix("postgresql://")
        prefix = "postgresql+psycopg2://"
    elif raw.startswith("postgres://"):
        body = raw.removeprefix("postgres://")
        prefix = "postgresql+psycopg2://"
    else:
        return raw

    # Direct db.<ref>.supabase.co is often IPv6-only; rewrite to Session pooler (IPv4).
    if "@" in body:
        userinfo, hostpart = body.rsplit("@", 1)
        host_port = hostpart.split("/", 1)[0].split("?", 1)[0]
        path = ""
        if "/" in hostpart.split("?", 1)[0]:
            path = "/" + hostpart.split("?", 1)[0].split("/", 1)[1]
        query = ""
        if "?" in hostpart:
            query = "?" + hostpart.split("?", 1)[1]
        hostname = host_port.rsplit(":", 1)[0]
        if hostname.startswith("db.") and hostname.endswith(".supabase.co"):
            ref = hostname.removeprefix("db.").removesuffix(".supabase.co")
            # Session pooler expects <role>.<project-ref> (postgres / teammate / …)
            user = userinfo.split(":", 1)[0]
            password = userinfo.split(":", 1)[1] if ":" in userinfo else ""
            if "." not in user:
                userinfo = f"{user}.{ref}:{password}"
            hostpart = (
                f"aws-0-ap-northeast-1.pooler.supabase.com:5432"
                f"{path or '/postgres'}{query}"
            )
            body = f"{userinfo}@{hostpart}"

    return prefix + body


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    # LAN phone: 172.30.1.* any port. Local FE: localhost/127.0.0.1 ports 3000–3009.
    # Empty string disables regex allowlist.
    cors_origin_regex: str = (
        r"http://((localhost|127\.0\.0\.1):300[0-9]|172\.30\.1\.\d+:\d+)"
    )

    # local = MariaDB(DB_*) · supabase = Postgres(SUPABASE_DB_URL)
    db_backend: DbBackend = "local"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = ""
    db_password: str = ""
    db_name: str = "ev-daegue_eta"

    # Supabase Session/URI mode connection string (password included). Server only.
    supabase_db_url: str = ""
    # Optional full override (wins over DB_BACKEND assembly)
    database_url: str | None = None

    tmap_app_key: str = ""
    data_go_kr_key: str = ""

    # 추천 모델 API (외부 서버 — X-API-Key)
    recommend_api_base_url: str = "http://3.39.251.72:8000"
    recommend_api_timeout: float = 10.0
    recommend_api_key: str = ""

    # EvCharger status collector (see domains/stations/sync.py)
    # Base e.g. https://apis.data.go.kr/B552584/EvCharger  (getChargerStatus appended)
    ev_charger_api_url: str = ""
    # Default OFF — PC·운영 동시 수집 방지. 수집 서버만 true.
    ev_status_sync_enabled: bool = False
    ev_status_interval_minutes: int = 5
    ev_status_period_minutes: int = 5
    # 대구 시도코드(행정구역 앞 2자리). 빈 문자열이면 zcode 미전송(전국).
    ev_status_zcode: str = "27"
    ev_status_num_of_rows: int = 9999
    # Soft cap (process memory). 5분×288≈일 + 여유. 개발계정 한도(~1000) 대비.
    ev_status_daily_call_limit: int = 400
    # Local auth JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 1 day

    # 소셜 OAuth 콜백 후 FE 리다이렉트 기준 origin
    frontend_origin: str = "http://localhost:3000"
    # itsdangerous state 서명용 시크릿
    oauth_state_secret: str = ""
    # HttpOnly JWT 쿠키 이름
    auth_cookie_name: str = "access_token"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Kakao OAuth
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = "http://localhost:8000/api/v1/auth/kakao/callback"

    # Naver OAuth
    naver_client_id: str = ""
    naver_client_secret: str = ""
    naver_redirect_uri: str = "http://localhost:8000/api/v1/auth/naver/callback"

    # PortOne V2 (포인트 충전)
    portone_api_secret: str = ""
    portone_webhook_secret: str = ""
    portone_store_id: str = ""
    portone_channel_key: str = ""


    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return normalize_sqlalchemy_url(self.database_url)

        if self.db_backend == "supabase":
            if not self.supabase_db_url.strip():
                raise ValueError(
                    "DB_BACKEND=supabase requires SUPABASE_DB_URL "
                    "(Postgres URI from Supabase → Database → Connection string)"
                )
            return normalize_sqlalchemy_url(self.supabase_db_url.strip())

        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
