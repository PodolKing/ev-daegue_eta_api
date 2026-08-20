# usage_orders API 스키마 (CamelModel → JSON camelCase)
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel

PayMode = Literal["amount", "usage"]


class ChargeRequestBody(CamelModel):
    """충전 요청 — 충전기·대표차 검증."""

    stat_id: str = Field(min_length=1, max_length=20)
    chger_id: str = Field(min_length=1, max_length=10)


class PrimaryCarSummary(CamelModel):
    id: int
    car_number: str | None = None
    custom_model_name: str | None = None
    is_primary: bool


class ChargeRequestResponse(CamelModel):
    ready: bool
    stat_id: str
    chger_id: str
    charger_status: str | None
    busi_id: str | None
    output_kw: float | None
    primary_car: PrimaryCarSummary | None
    balance: int
    message: str


class PreAuthorizeRequest(CamelModel):
    """가결제 — 금액/사용량 모드에 따라 포인트 선차감."""

    stat_id: str = Field(min_length=1, max_length=20)
    chger_id: str = Field(min_length=1, max_length=10)
    limit_amount_krw: int = Field(
        ge=1,
        description="금액 모드: 결제 P / 사용량 모드: FE 호환(서버는 잔액 홀드)",
    )
    mode: PayMode = "usage"
    idempotency_key: str | None = Field(default=None, max_length=64)


class UsageOrderPublic(CamelModel):
    id: int
    user_id: int
    stat_id: str | None
    chger_id: str | None
    busi_id: str | None
    stat_nm: str | None = None
    kwh: Decimal
    kwh_source: str
    rate_member_won: Decimal
    amount_list_krw: int
    amount_charge_krw: int
    discount_krw: int
    points_spent: int
    status: str
    memo: str | None = None
    hold_amount_krw: int | None = None
    refund_amount_krw: int | None = None
    shortfall_krw: int | None = None
    balance: int | None = None
    created_at: datetime
    updated_at: datetime


class CompleteRequest(CamelModel):
    """충전 완료 — 사용량 입력 또는 금액 모드(서버가 kWh·요금 산정)."""

    mode: PayMode = "usage"
    kwh: float | None = Field(default=None, gt=0, description="사용량 모드 필수")
    kwh_source: str | None = Field(default="manual", max_length=32)


class PayResponse(CamelModel):
    processed: bool
    order: UsageOrderPublic
    message: str


class UsageOrderListResponse(CamelModel):
    """본인 이용·결제 내역."""

    items: list[UsageOrderPublic]
    count: int


class WaitChargerRate(CamelModel):
    chger_id: str
    output_kw: float | None = None
    rate_member_won: Decimal | None = None
    used_avg: bool = False


class WaitChargerRatesResponse(CamelModel):
    """대기 기 member 단가 (조회만)."""

    stat_id: str
    items: list[WaitChargerRate]
    count: int
