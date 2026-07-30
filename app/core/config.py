from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = ""
    db_password: str = ""
    db_name: str = "ev-daegue_eta"
    database_url: str | None = None

    tmap_app_key: str = ""
    data_go_kr_key: str = ""

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

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
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
