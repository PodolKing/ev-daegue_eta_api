# router ↔ service 요청 조립·응답 스키마 변환
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.domains.auth.models import User, UserRole
from app.domains.points import service as points_service
from app.domains.points.schema import (
    BalanceResponse,
    ChargeCompleteRequest,
    ChargeCompleteResponse,
    ChargeCreateRequest,
    ChargeCreateResponse,
    ChargeFailRequest,
    ChargeFailResponse,
    ChargeHistoryItem,
    ChargeHistoryResponse,
    CreditRequest,
    CreditResponse,
)


def _role_value(user: User) -> str:
    role = getattr(user.role, "value", user.role)
    return str(role or "")


def _require_admin(user: User) -> None:
    if _role_value(user) != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="관리자만 사용할 수 있습니다")


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="DB 미설정")
    return db


def balance(db: Session | None, user: User) -> BalanceResponse:
    session = _require_db(db)
    value = points_service.get_balance(session, user_pk=int(user.id))
    return BalanceResponse(balance=value)


def credit(
    db: Session | None,
    user: User,
    body: CreditRequest,
) -> CreditResponse:
    _require_admin(user)
    session = _require_db(db)
    result = points_service.credit_points(
        session,
        admin_pk=int(user.id),
        nickname=body.nickname,
        points=int(body.points),
        memo=body.memo,
    )
    return CreditResponse.model_validate(result)


def create_charge(
    db: Session | None,
    user: User,
    body: ChargeCreateRequest,
) -> ChargeCreateResponse:
    session = _require_db(db)
    result = points_service.create_charge(
        session,
        user_pk=int(user.id),
        amount_krw=int(body.amount_krw),
    )
    return ChargeCreateResponse.model_validate(result)


def complete_charge(
    db: Session | None,
    user: User,
    body: ChargeCompleteRequest,
) -> ChargeCompleteResponse:
    session = _require_db(db)
    result = points_service.complete_charge(
        session,
        payment_id=body.payment_id,
        expect_user_pk=int(user.id),
    )
    return ChargeCompleteResponse.model_validate(result)


def fail_charge(
    db: Session | None,
    user: User,
    body: ChargeFailRequest,
) -> ChargeFailResponse:
    session = _require_db(db)
    result = points_service.fail_charge(
        session,
        payment_id=body.payment_id,
        expect_user_pk=int(user.id),
    )
    return ChargeFailResponse.model_validate(result)


def list_charges(
    db: Session | None,
    user: User,
    limit: int,
) -> ChargeHistoryResponse:
    session = _require_db(db)
    rows = points_service.list_charges(
        session,
        user_pk=int(user.id),
        limit=limit,
    )
    items = [ChargeHistoryItem.model_validate(row) for row in rows]
    return ChargeHistoryResponse(items=items, count=len(items))


async def portone_webhook(
    db: Session | None,
    request: Request,
) -> dict[str, str]:
    session = _require_db(db)
    raw = (await request.body()).decode("utf-8")
    headers = {k: v for k, v in request.headers.items()}
    return points_service.handle_portone_webhook(
        session,
        raw_body=raw,
        headers=headers,
    )
