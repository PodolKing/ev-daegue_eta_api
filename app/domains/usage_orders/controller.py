# router ↔ service
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.models import User
from app.domains.usage_orders import service as usage_service
from app.domains.usage_orders.schema import (
    ChargeRequestBody,
    ChargeRequestResponse,
    CompleteRequest,
    PayResponse,
    PreAuthorizeRequest,
    UsageOrderListResponse,
    UsageOrderPublic,
)


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="DB 미설정")
    return db


def request_charge(
    db: Session | None,
    user: User,
    body: ChargeRequestBody,
) -> ChargeRequestResponse:
    session = _require_db(db)
    result = usage_service.request_charge(
        session,
        user_pk=int(user.id),
        stat_id=body.stat_id,
        chger_id=body.chger_id,
    )
    return ChargeRequestResponse.model_validate(result)


def pre_authorize(
    db: Session | None,
    user: User,
    body: PreAuthorizeRequest,
) -> UsageOrderPublic:
    session = _require_db(db)
    result = usage_service.pre_authorize(
        session,
        user_pk=int(user.id),
        stat_id=body.stat_id,
        chger_id=body.chger_id,
        limit_amount_krw=int(body.limit_amount_krw),
        idempotency_key=body.idempotency_key,
    )
    return UsageOrderPublic.model_validate(result)


def complete(
    db: Session | None,
    user: User,
    order_id: int,
    body: CompleteRequest,
) -> UsageOrderPublic:
    session = _require_db(db)
    result = usage_service.complete_order(
        session,
        user_pk=int(user.id),
        order_id=order_id,
        kwh=float(body.kwh),
        kwh_source=body.kwh_source,
    )
    return UsageOrderPublic.model_validate(result)


def pay(
    db: Session | None,
    user: User,
    order_id: int,
) -> PayResponse:
    session = _require_db(db)
    result = usage_service.pay_order(
        session,
        user_pk=int(user.id),
        order_id=order_id,
    )
    return PayResponse(
        processed=bool(result["processed"]),
        order=UsageOrderPublic.model_validate(result["order"]),
        message=str(result["message"]),
    )


def list_mine(
    db: Session | None,
    user: User,
    *,
    status: str | None,
    limit: int,
) -> UsageOrderListResponse:
    session = _require_db(db)
    rows = usage_service.list_my_orders(
        session,
        user_pk=int(user.id),
        status=status,
        limit=limit,
    )
    items = [UsageOrderPublic.model_validate(row) for row in rows]
    return UsageOrderListResponse(items=items, count=len(items))


def get_mine(
    db: Session | None,
    user: User,
    order_id: int,
) -> UsageOrderPublic:
    session = _require_db(db)
    row = usage_service.get_my_order(
        session,
        user_pk=int(user.id),
        order_id=order_id,
    )
    return UsageOrderPublic.model_validate(row)
