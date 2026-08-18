# 충전 이용·요금 정산 HTTP 라우터
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.deps import get_current_user
from app.domains.auth.models import User
from app.domains.usage_orders import controller as usage_controller
from app.domains.usage_orders.schema import (
    ChargeRequestBody,
    ChargeRequestResponse,
    CompleteRequest,
    PayResponse,
    PreAuthorizeRequest,
    UsageOrderListResponse,
    UsageOrderPublic,
    WaitChargerRatesResponse,
)

router = APIRouter(prefix="/api/v1/usage-orders", tags=["usage-orders"])


@router.get("/list", response_model=UsageOrderListResponse)
def list_orders(
    status: str | None = Query(
        None,
        description="draft | confirmed | cancelled | refunded",
    ),
    limit: int = Query(20, ge=1, le=100),
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsageOrderListResponse:
    """본인 이용·결제 내역 조회 (최신순)."""
    return usage_controller.list_mine(db, user, status=status, limit=limit)


@router.get("/rates", response_model=WaitChargerRatesResponse)
def wait_charger_rates(
    stat_id: str = Query(..., min_length=1, max_length=20),
    db: Session | None = Depends(get_db),
) -> WaitChargerRatesResponse:
    """대기 기 member 단가 조회. 지갑·주문 없음. 공공 불변."""
    return usage_controller.list_wait_rates(db, stat_id=stat_id)


@router.get("/{order_id}", response_model=UsageOrderPublic)
def get_order(
    order_id: int,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsageOrderPublic:
    """본인 이용·결제 단건 조회."""
    return usage_controller.get_mine(db, user, order_id)


@router.post("/request", response_model=ChargeRequestResponse)
def request_charge(
    body: ChargeRequestBody,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChargeRequestResponse:
    """1. 충전 요청 — 충전기 대기·대표차·잔액 확인."""
    return usage_controller.request_charge(db, user, body)


@router.post("/pre-authorize", response_model=UsageOrderPublic)
def pre_authorize(
    body: PreAuthorizeRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsageOrderPublic:
    """2. 가결제 — 한도 포인트 선차감, 충전 시작."""
    return usage_controller.pre_authorize(db, user, body)


@router.patch("/{order_id}/complete", response_model=UsageOrderPublic)
def complete_order(
    order_id: int,
    body: CompleteRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsageOrderPublic:
    """3. 충전 완료 — member 단가·실요금 산정."""
    return usage_controller.complete(db, user, order_id, body)


@router.post("/{order_id}/pay", response_model=PayResponse)
def pay_order(
    order_id: int,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PayResponse:
    """4. 요금 정산 — 가결제 차액 환불, confirmed."""
    return usage_controller.pay(db, user, order_id)


@router.post("/{order_id}/cancel", response_model=PayResponse)
def cancel_order(
    order_id: int,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PayResponse:
    """draft 가결제 취소 — 홀드 전액 환불. 공공 status 불변."""
    return usage_controller.cancel(db, user, order_id)