# 포인트 잔액·충전·웹훅 HTTP 라우터
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.deps import get_current_user
from app.domains.auth.models import User
from app.domains.points import controller as points_controller
from app.domains.points.schema import (
    BalanceResponse,
    ChargeCompleteRequest,
    ChargeCompleteResponse,
    ChargeCreateRequest,
    ChargeCreateResponse,
    ChargeFailRequest,
    ChargeFailResponse,
    ChargeHistoryResponse,
    CreditRequest,
    CreditResponse,
)

router = APIRouter(prefix="/api/v1/points", tags=["points"])


@router.get("/balance", response_model=BalanceResponse)
def balance(
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BalanceResponse:
    """내 포인트 잔액 조회."""
    return points_controller.balance(db, user)


@router.post("/credit", response_model=CreditResponse)
def credit(
    body: CreditRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CreditResponse:
    """ADMIN: 닉네임으로 대상 지갑에 포트원 없이 적립."""
    return points_controller.credit(db, user, body)


@router.post("/charges", response_model=ChargeCreateResponse)
def create_charge(
    body: ChargeCreateRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChargeCreateResponse:
    """포인트 충전 주문 생성 (PortOne paymentId 발급)."""
    return points_controller.create_charge(db, user, body)


@router.post("/charges/complete", response_model=ChargeCompleteResponse)
def complete_charge(
    body: ChargeCompleteRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChargeCompleteResponse:
    """클라이언트 결제 완료 후 서버 검증·포인트 적립."""
    return points_controller.complete_charge(db, user, body)


@router.post("/charges/fail", response_model=ChargeFailResponse)
def fail_charge(
    body: ChargeFailRequest,
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChargeFailResponse:
    """위젯 실패·취소 시 pending → failed. 지갑은 건드리지 않음."""
    return points_controller.fail_charge(db, user, body)


@router.get("/charges", response_model=ChargeHistoryResponse)
def list_charges(
    limit: int = Query(20, ge=1, le=100),
    db: Session | None = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChargeHistoryResponse:
    """내 포인트 충전 내역 (payments)."""
    return points_controller.list_charges(db, user, limit)


@router.post("/webhooks/portone")
async def portone_webhook(
    request: Request,
    db: Session | None = Depends(get_db),
) -> dict[str, str]:
    """PortOne V2 웹훅. JWT 없음 — 서명 검증."""
    return await points_controller.portone_webhook(db, request)
