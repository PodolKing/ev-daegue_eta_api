# 충전 요청 → 가결제 → 완료 → 포인트 정산
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.auth.models import User
from app.domains.cars.models import Car
from app.domains.points.models import PointTransaction, PointWallet
from app.domains.stations.models import EvChargerInfo, EvChargerStatus
from app.domains.usage_orders.constants import (
    CHARGER_STATUS_CHARGING,
    CHARGER_STATUS_WAIT,
    KWH_SOURCE_MANUAL,
    KWH_SOURCE_PRESET,
    MAX_HOLD_KRW,
    MAX_KWH,
    MEMBER_TYPE,
    MIN_HOLD_KRW,
    MIN_KWH,
    PLACEHOLDER_KWH,
    REF_TYPE_USAGE_ORDER,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_DRAFT,
    STATUS_REFUNDED,
    TX_TYPE_REFUND,
    TX_TYPE_USE,
)
from app.domains.usage_orders.models import OperatorTariff, UsageOrder
from app.domains.usage_orders.tariff import pick_member_rate_won


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ensure_wallet(db: Session, *, user_pk: int) -> PointWallet:
    wallet = db.get(PointWallet, user_pk)
    if wallet is not None:
        return wallet
    now = _now()
    wallet = PointWallet(
        user_id=user_pk,
        balance=0,
        version=0,
        created_at=now,
        updated_at=now,
    )
    db.add(wallet)
    db.flush()
    return wallet


def _lock_wallet(db: Session, *, user_pk: int) -> PointWallet:
    _ensure_wallet(db, user_pk=user_pk)
    return db.execute(
        select(PointWallet)
        .where(PointWallet.user_id == user_pk)
        .with_for_update()
    ).scalar_one()


def _primary_car(db: Session, *, user_pk: int) -> Car | None:
    return db.scalar(
        select(Car).where(
            Car.user_id == user_pk,
            Car.is_active.is_(True),
            Car.is_primary.is_(True),
        )
    )


def _get_charger_pair(
    db: Session,
    *,
    stat_id: str,
    chger_id: str,
) -> tuple[EvChargerInfo, EvChargerStatus]:
    info = db.get(EvChargerInfo, {"stat_id": stat_id, "chger_id": chger_id})
    status = db.get(EvChargerStatus, {"stat_id": stat_id, "chger_id": chger_id})
    if info is None or status is None:
        raise HTTPException(status_code=404, detail="충전기를 찾을 수 없습니다")
    return info, status


def _hold_tx_key(order_id: int) -> str:
    return f"usage_hold:{order_id}"


def _refund_tx_key(order_id: int) -> str:
    return f"usage_refund:{order_id}"


def _order_to_dict(
    order: UsageOrder,
    *,
    hold_amount_krw: int | None = None,
    refund_amount_krw: int | None = None,
    balance: int | None = None,
) -> dict[str, object]:
    hold = (
        hold_amount_krw
        if hold_amount_krw is not None
        else int(order.amount_list_krw)
    )
    refund = refund_amount_krw
    if refund is None and order.status == STATUS_CONFIRMED:
        refund = max(0, hold - int(order.points_spent))
    elif refund is None and order.kwh_source == KWH_SOURCE_MANUAL:
        refund = max(0, hold - int(order.amount_charge_krw))

    return {
        "id": int(order.id),
        "user_id": int(order.user_id),
        "stat_id": order.stat_id,
        "chger_id": order.chger_id,
        "busi_id": order.busi_id,
        "kwh": order.kwh,
        "kwh_source": order.kwh_source,
        "rate_member_won": order.rate_member_won,
        "amount_list_krw": int(order.amount_list_krw),
        "amount_charge_krw": int(order.amount_charge_krw),
        "discount_krw": int(order.discount_krw),
        "points_spent": int(order.points_spent),
        "status": order.status,
        "memo": order.memo,
        "hold_amount_krw": hold,
        "refund_amount_krw": refund,
        "balance": balance,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def list_my_orders(
    db: Session,
    *,
    user_pk: int,
    status: str | None = None,
    limit: int = 20,
) -> list[dict[str, object]]:
    """본인 이용·결제(usage_orders) 내역 최신순."""
    limit = max(1, min(int(limit), 100))
    stmt = select(UsageOrder).where(UsageOrder.user_id == user_pk)
    if status:
        status_key = status.strip().lower()
        allowed = {
            STATUS_DRAFT,
            STATUS_CONFIRMED,
            STATUS_CANCELLED,
            STATUS_REFUNDED,
        }
        if status_key not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"status는 {', '.join(sorted(allowed))} 중 하나여야 합니다",
            )
        stmt = stmt.where(UsageOrder.status == status_key)
    stmt = stmt.order_by(UsageOrder.created_at.desc(), UsageOrder.id.desc()).limit(
        limit
    )
    rows = db.scalars(stmt).all()
    return [_order_to_dict(row) for row in rows]


def get_my_order(
    db: Session,
    *,
    user_pk: int,
    order_id: int,
) -> dict[str, object]:
    """본인 이용·결제 단건 조회."""
    order = db.scalar(
        select(UsageOrder).where(
            UsageOrder.id == order_id,
            UsageOrder.user_id == user_pk,
        )
    )
    if order is None:
        raise HTTPException(status_code=404, detail="이용 주문을 찾을 수 없습니다")
    return _order_to_dict(order)


def request_charge(
    db: Session,
    *,
    user_pk: int,
    stat_id: str,
    chger_id: str,
) -> dict[str, object]:
    """1단계: 충전기 대기 상태·대표차·잔액 확인."""
    try:
        user = db.get(User, user_pk)
        if user is None or not user.is_active or user.deleted_at is not None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        stat_key = stat_id.strip()
        chger_key = chger_id.strip()
        info, status = _get_charger_pair(db, stat_id=stat_key, chger_id=chger_key)

        car = _primary_car(db, user_pk=user_pk)
        wallet = _ensure_wallet(db, user_pk=user_pk)
        db.commit()

        ready = status.charger_status == CHARGER_STATUS_WAIT and car is not None
        if status.charger_status != CHARGER_STATUS_WAIT:
            message = "충전기가 충전 대기 상태가 아닙니다"
        elif car is None:
            message = "내 차량에서 대표 차량을 선택하면 충전 서비스를 이용할 수 있습니다"
        else:
            message = "충전 요청 가능. 가결제(한도)를 진행하세요"

        primary = None
        if car is not None:
            primary = {
                "id": int(car.id),
                "car_number": car.car_number,
                "custom_model_name": car.custom_model_name,
                "is_primary": bool(car.is_primary),
            }

        output = float(info.output) if info.output is not None else None
        return {
            "ready": ready,
            "stat_id": stat_key,
            "chger_id": chger_key,
            "charger_status": status.charger_status,
            "busi_id": info.busi_id,
            "output_kw": output,
            "primary_car": primary,
            "balance": int(wallet.balance),
            "message": message,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def pre_authorize(
    db: Session,
    *,
    user_pk: int,
    stat_id: str,
    chger_id: str,
    limit_amount_krw: int,
    idempotency_key: str | None,
) -> dict[str, object]:
    """2단계: 한도만큼 포인트 선차감 + draft 주문 + 충전기 충전중."""
    if limit_amount_krw < MIN_HOLD_KRW or limit_amount_krw > MAX_HOLD_KRW:
        raise HTTPException(
            status_code=400,
            detail=f"충전 한도는 {MIN_HOLD_KRW}~{MAX_HOLD_KRW}원입니다",
        )

    try:
        user = db.execute(
            select(User).where(User.id == user_pk).with_for_update()
        ).scalar_one_or_none()
        if user is None or not user.is_active or user.deleted_at is not None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        if idempotency_key:
            existing = db.scalar(
                select(UsageOrder).where(UsageOrder.idempotency_key == idempotency_key)
            )
            if existing is not None:
                if int(existing.user_id) != user_pk:
                    raise HTTPException(status_code=409, detail="idempotencyKey 충돌")
                wallet = _ensure_wallet(db, user_pk=user_pk)
                return _order_to_dict(
                    existing,
                    hold_amount_krw=int(existing.amount_list_krw),
                    balance=int(wallet.balance),
                )

        car = _primary_car(db, user_pk=user_pk)
        if car is None:
            raise HTTPException(
                status_code=400,
                detail="내 차량에서 대표 차량을 선택하면 충전 서비스를 이용할 수 있습니다",
            )

        stat_key = stat_id.strip()
        chger_key = chger_id.strip()
        info, status = _get_charger_pair(db, stat_id=stat_key, chger_id=chger_key)
        if status.charger_status != CHARGER_STATUS_WAIT:
            raise HTTPException(
                status_code=409,
                detail=f"충전기가 대기 상태가 아닙니다 (status={status.charger_status})",
            )

        wallet = _lock_wallet(db, user_pk=user_pk)
        if int(wallet.balance) < limit_amount_krw:
            raise HTTPException(
                status_code=402,
                detail="포인트가 부족합니다. 포인트 충전 후 다시 시도하세요",
            )

        now = _now()
        order = UsageOrder(
            user_id=user_pk,
            stat_id=stat_key,
            chger_id=chger_key,
            busi_id=info.busi_id,
            # DB CHECK: kwh > 0 — 완료 전 placeholder
            kwh=Decimal(PLACEHOLDER_KWH),
            kwh_source=KWH_SOURCE_PRESET,
            rate_member_won=Decimal("0.00"),
            rate_non_member_won=None,
            amount_list_krw=limit_amount_krw,  # 가결제 한도 보관
            amount_charge_krw=limit_amount_krw,
            discount_krw=0,
            points_spent=0,
            status=STATUS_DRAFT,
            memo="충전 가결제",
            idempotency_key=idempotency_key or f"preauth_{uuid4().hex}",
            created_at=now,
            updated_at=now,
        )
        db.add(order)
        db.flush()

        new_balance = int(wallet.balance) - limit_amount_krw
        wallet.balance = new_balance
        wallet.version = int(wallet.version) + 1
        wallet.updated_at = now
        user.point = new_balance
        user.updated_at = now

        db.add(
            PointTransaction(
                wallet_id=user_pk,
                type=TX_TYPE_USE,
                amount=limit_amount_krw,
                balance_after=new_balance,
                ref_type=REF_TYPE_USAGE_ORDER,
                ref_id=int(order.id),
                idempotency_key=_hold_tx_key(int(order.id)),
                memo=f"충전 가결제 한도 차감 order={order.id}",
                created_at=now,
            )
        )

        status.charger_status = CHARGER_STATUS_CHARGING
        status.last_updated = now

        db.commit()
        db.refresh(order)
        return _order_to_dict(
            order,
            hold_amount_krw=limit_amount_krw,
            balance=new_balance,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def complete_order(
    db: Session,
    *,
    user_pk: int,
    order_id: int,
    kwh: float,
    kwh_source: str | None,
) -> dict[str, object]:
    """3단계: kWh·member 단가로 실요금 산정, 충전기 대기 복구."""
    if kwh < MIN_KWH or kwh > MAX_KWH:
        raise HTTPException(
            status_code=400,
            detail=f"kwh는 {MIN_KWH}~{MAX_KWH} 범위여야 합니다",
        )

    try:
        order = db.execute(
            select(UsageOrder)
            .where(UsageOrder.id == order_id)
            .with_for_update()
        ).scalar_one_or_none()
        if order is None or int(order.user_id) != user_pk:
            raise HTTPException(status_code=404, detail="이용 주문을 찾을 수 없습니다")

        if order.status == STATUS_CONFIRMED:
            raise HTTPException(status_code=409, detail="이미 정산 완료된 주문입니다")
        if order.status != STATUS_DRAFT:
            raise HTTPException(
                status_code=409,
                detail=f"완료할 수 없는 상태입니다 ({order.status})",
            )
        # 이미 요금 산정됨(멱등) — kwh_source=manual
        if order.kwh_source == KWH_SOURCE_MANUAL and Decimal(str(order.rate_member_won)) > 0:
            hold = int(order.amount_list_krw)
            wallet = _ensure_wallet(db, user_pk=user_pk)
            db.commit()
            return _order_to_dict(
                order,
                hold_amount_krw=hold,
                balance=int(wallet.balance),
            )

        if not order.stat_id or not order.chger_id:
            raise HTTPException(status_code=400, detail="주문에 충전기 정보가 없습니다")

        info, status = _get_charger_pair(
            db,
            stat_id=str(order.stat_id),
            chger_id=str(order.chger_id),
        )
        busi_id = order.busi_id or info.busi_id
        if not busi_id:
            raise HTTPException(status_code=400, detail="사업자(busiId)를 확인할 수 없습니다")

        tariff = db.get(
            OperatorTariff,
            {"busi_id": busi_id, "member_type": MEMBER_TYPE},
        )
        if tariff is None:
            raise HTTPException(
                status_code=404,
                detail="회원 요금 정보를 찾을 수 없습니다",
            )

        output_kw = float(info.output) if info.output is not None else None
        try:
            rate = pick_member_rate_won(output_kw=output_kw, tariff_row=tariff)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        kwh_dec = Decimal(str(kwh)).quantize(Decimal("0.01"))
        # 원 단위 버림: floor(kwh * rate)
        actual = int(
            (kwh_dec * rate).to_integral_value(rounding=ROUND_FLOOR)
        )
        if actual < 0:
            actual = 0

        hold = int(order.amount_list_krw)
        if actual > hold:
            # 한도 초과분은 한도로 캡 (미납 방지)
            actual = hold

        now = _now()
        order.kwh = kwh_dec
        # DB CHECK: manual|preset|operator_session
        src = (kwh_source or KWH_SOURCE_MANUAL).strip() or KWH_SOURCE_MANUAL
        if src not in (KWH_SOURCE_MANUAL, "preset", "operator_session"):
            src = KWH_SOURCE_MANUAL
        order.kwh_source = src if src != KWH_SOURCE_PRESET else KWH_SOURCE_MANUAL
        order.busi_id = busi_id
        order.rate_member_won = rate
        order.rate_non_member_won = None  # member만 사용
        # amount_list_krw = 가결제 한도 유지
        # amount_charge_krw = 실요금 (discount는 CHECK상 charge 이하여야 해서 0 유지)
        order.amount_charge_krw = actual
        order.discount_krw = 0
        order.status = STATUS_DRAFT
        order.updated_at = now
        order.memo = f"충전 완료 kWh={kwh_dec} rate={rate} fee={actual}"

        status.charger_status = CHARGER_STATUS_WAIT
        status.last_updated = now

        wallet = _ensure_wallet(db, user_pk=user_pk)
        db.commit()
        db.refresh(order)
        return _order_to_dict(
            order,
            hold_amount_krw=hold,
            balance=int(wallet.balance),
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None


def pay_order(
    db: Session,
    *,
    user_pk: int,
    order_id: int,
) -> dict[str, object]:
    """4단계: 가결제 한도 − 실요금 차액 환불, confirmed."""
    try:
        user = db.execute(
            select(User).where(User.id == user_pk).with_for_update()
        ).scalar_one_or_none()
        if user is None or not user.is_active or user.deleted_at is not None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        order = db.execute(
            select(UsageOrder)
            .where(UsageOrder.id == order_id)
            .with_for_update()
        ).scalar_one_or_none()
        if order is None or int(order.user_id) != user_pk:
            raise HTTPException(status_code=404, detail="이용 주문을 찾을 수 없습니다")

        wallet = _lock_wallet(db, user_pk=user_pk)

        if order.status == STATUS_CONFIRMED:
            return {
                "processed": False,
                "order": _order_to_dict(
                    order,
                    hold_amount_krw=int(order.amount_list_krw),
                    refund_amount_krw=int(order.discount_krw),
                    balance=int(wallet.balance),
                ),
                "message": "이미 정산 완료된 주문입니다",
            }

        if order.status != STATUS_DRAFT:
            raise HTTPException(
                status_code=409,
                detail="정산할 수 없는 상태입니다",
            )
        if order.kwh_source != KWH_SOURCE_MANUAL or Decimal(str(order.rate_member_won)) <= 0:
            raise HTTPException(
                status_code=409,
                detail="충전 완료 후 정산할 수 있습니다",
            )

        hold = int(order.amount_list_krw)
        actual = int(order.amount_charge_krw)
        refund = max(0, hold - actual)

        now = _now()
        if refund > 0:
            existing_refund = db.scalar(
                select(PointTransaction).where(
                    PointTransaction.idempotency_key == _refund_tx_key(int(order.id))
                )
            )
            if existing_refund is None:
                new_balance = int(wallet.balance) + refund
                wallet.balance = new_balance
                wallet.version = int(wallet.version) + 1
                wallet.updated_at = now
                user.point = new_balance
                user.updated_at = now
                db.add(
                    PointTransaction(
                        wallet_id=user_pk,
                        type=TX_TYPE_REFUND,
                        amount=refund,
                        balance_after=new_balance,
                        ref_type=REF_TYPE_USAGE_ORDER,
                        ref_id=int(order.id),
                        idempotency_key=_refund_tx_key(int(order.id)),
                        memo=f"충전 가결제 차액 환불 order={order.id}",
                        created_at=now,
                    )
                )
            else:
                new_balance = int(wallet.balance)
        else:
            new_balance = int(wallet.balance)

        order.points_spent = actual
        # discount_krw <= amount_charge_krw CHECK → 환불액은 원장에만 기록
        order.discount_krw = 0
        order.status = STATUS_CONFIRMED
        order.updated_at = now
        order.memo = f"정산 완료 spent={actual} refund={refund}"

        db.commit()
        db.refresh(order)
        return {
            "processed": True,
            "order": _order_to_dict(
                order,
                hold_amount_krw=hold,
                refund_amount_krw=refund,
                balance=new_balance,
            ),
            "message": "요금 정산이 완료되었습니다",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="내부 서버 에러(관리자에게 문의)",
        ) from None
