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
    # LAN mobile: allow any host in 172.30.1.0/24 (DHCP IP churn). Empty = disabled.
    cors_origin_regex: str = r"http://172\.30\.1\.\d+:\d+"

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
