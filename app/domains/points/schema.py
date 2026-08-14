# points API 요청·응답 (CamelModel → JSON camelCase)
from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class BalanceResponse(CamelModel):
    balance: int


class ChargeCreateRequest(CamelModel):
    """충전 요청. 금액은 서버에서 포인트로 환산한다."""

    amount_krw: int = Field(ge=1, description="결제 금액(원)")


class ChargeCreateResponse(CamelModel):
    """FE PortOne requestPayment 에 필요한 값."""

    payment_id: str
    order_name: str
    amount_krw: int
    points_granted: int
    bonus_points: int
    store_id: str
    channel_key: str
    status: str
    customer_email: str
    customer_name: str


class ChargeCompleteRequest(CamelModel):
    payment_id: str = Field(min_length=1, max_length=64)


class ChargeCompleteResponse(CamelModel):
    processed: bool
    payment_id: str
    status: str
    amount_krw: int
    points_granted: int
    bonus_points: int
    balance: int
    message: str


class ChargeHistoryItem(CamelModel):
    id: int
    payment_id: str | None = None
    amount_krw: int
    points_granted: int
    bonus_points: int
    status: str
    paid_at: datetime | None = None
    created_at: datetime


class ChargeHistoryResponse(CamelModel):
    items: list[ChargeHistoryItem]
    count: int


class ChargeFailRequest(CamelModel):
    payment_id: str = Field(min_length=1, max_length=64)


class ChargeFailResponse(CamelModel):
    processed: bool
    payment_id: str
    status: str
    message: str


class CreditRequest(CamelModel):
    """포트원 없이 대상 유저 지갑에 포인트 적립 (ADMIN)."""

    nickname: str = Field(min_length=1, max_length=30, description="적립 대상 닉네임")
    points: int = Field(ge=1, le=1_000_000, description="적립 포인트")
    memo: str | None = Field(default=None, max_length=255)


class CreditResponse(CamelModel):
    processed: bool = True
    points: int
    balance: int
    nickname: str
    message: str
