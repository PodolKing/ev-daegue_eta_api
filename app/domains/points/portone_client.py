# PortOne V2 SDK 래퍼 — 결제 조회·웹훅 검증
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import portone_server_sdk as portone
from portone_server_sdk import PaymentClient
from portone_server_sdk.payment import FailedPayment, PaidPayment

from app.core.config import get_settings


@dataclass(frozen=True)
class PortOnePaymentView:
    """서버 검증용 최소 결제 정보."""

    payment_id: str
    status: str  # PAID | FAILED | OTHER
    amount_total: int
    transaction_id: str | None
    order_name: str | None


def _payment_client() -> PaymentClient:
    secret = get_settings().portone_api_secret.strip()
    if not secret:
        raise RuntimeError("PORTONE_API_SECRET 미설정")
    return PaymentClient(secret=secret)


def get_payment(payment_id: str) -> PortOnePaymentView:
    """포트원 결제 단건 조회."""
    payment = _payment_client().get_payment(payment_id=payment_id)
    if isinstance(payment, PaidPayment):
        return PortOnePaymentView(
            payment_id=payment.id,
            status="PAID",
            amount_total=int(payment.amount.total),
            transaction_id=payment.transaction_id or payment.pg_tx_id,
            order_name=payment.order_name,
        )
    if isinstance(payment, FailedPayment):
        return PortOnePaymentView(
            payment_id=payment.id,
            status="FAILED",
            amount_total=int(payment.amount.total),
            transaction_id=getattr(payment, "transaction_id", None),
            order_name=getattr(payment, "order_name", None),
        )
    # Ready / Cancelled / VirtualAccount 등
    amount_total = 0
    if getattr(payment, "amount", None) is not None:
        amount_total = int(payment.amount.total)
    return PortOnePaymentView(
        payment_id=getattr(payment, "id", payment_id),
        status=str(getattr(payment, "status", "OTHER") or "OTHER"),
        amount_total=amount_total,
        transaction_id=getattr(payment, "transaction_id", None),
        order_name=getattr(payment, "order_name", None),
    )


def verify_webhook(raw_body: str, headers: dict[str, str] | Any) -> Any:
    """
    웹훅 서명 검증. raw_body는 JSON 파싱 전 문자열이어야 한다.
    검증 실패 시 WebhookVerificationError.
    """
    secret = get_settings().portone_webhook_secret.strip()
    if not secret:
        raise RuntimeError("PORTONE_WEBHOOK_SECRET 미설정")
    return portone.webhook.verify(secret, raw_body, headers)


def extract_webhook_payment_id(webhook: Any) -> str | None:
    """Transaction.* 웹훅에서 payment_id 추출."""
    data = getattr(webhook, "data", None)
    if data is None:
        return None
    payment_id = getattr(data, "payment_id", None)
    if payment_id:
        return str(payment_id)
    return None
