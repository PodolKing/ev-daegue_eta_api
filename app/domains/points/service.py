# 포인트 지갑·충전 주문·원장 비즈니스 로직
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.auth.models import User
import portone_server_sdk as portone

from app.domains.points import portone_client
from app.domains.points.constants import (
    MAX_CHARGE_KRW,
    MAX_DIRECT_POINTS,
    MIN_CHARGE_KRW,
    MIN_DIRECT_POINTS,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PENDING,
    PG_PROVIDER_PORTONE,
    REF_TYPE_ADMIN,
    REF_TYPE_PAYMENT,
    TX_TYPE_ADJUST,
    TX_TYPE_CHARGE,
    charge_idempotency_key,
    points_for_amount_krw,
)
from app.domains.points.models import Payment, PointTransaction, PointWallet


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_portone_config() -> None:
    settings = get_settings()
    if not settings.portone_api_secret.strip():
        raise HTTPException(status_code=503, detail="PORTONE_API_SECRET 미설정")
    if not settings.portone_store_id.strip():
        raise HTTPException(status_code=503, detail="PORTONE_STORE_ID 미설정")


def ensure_wallet(db: Session, *, user_pk: int) -> PointWallet:
    """지갑이 없으면 잔액 0으로 생성."""
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


def get_balance(db: Session, *, user_pk: int) -> int:
    wallet = ensure_wallet(db, user_pk=user_pk)
    db.commit()
    return int(wallet.balance)


def _buyer_email_for_pg(user: User) -> str:
    """이니시스 필수 buyer email. users에 email 컬럼 없음 → user_id 또는 합성값."""
    uid = (getattr(user, "user_id", None) or "").strip()
    if "@" in uid:
        return uid
    return f"user{int(user.id)}@noreply.local"


def _buyer_name_for_pg(user: User) -> str:
    nick = (user.nickname or "").strip()
    return nick or f"user{int(user.id)}"


def credit_points(
    db: Session,
    *,
    admin_pk: int,
    nickname: str,
    points: int,
    memo: str | None = None,
) -> dict[str, object]:
    """ADMIN이 닉네임 지갑을 ±조정. 원장 type=adjust. 음수는 0 하한. payments 불변."""
    if points == 0 or abs(points) < MIN_DIRECT_POINTS or abs(points) > MAX_DIRECT_POINTS:
        raise HTTPException(
            status_code=400,
            detail=f"조정 포인트는 ±{MIN_DIRECT_POINTS}~{MAX_DIRECT_POINTS}입니다 (0 불가)",
        )

    nick = (nickname or "").strip()
    if not nick:
        raise HTTPException(status_code=400, detail="닉네임은 필수입니다")

    try:
        user = db.execute(
            select(User).where(User.nickname == nick).with_for_update()
        ).scalar_one_or_none()
        if user is None or not user.is_active or user.deleted_at is not None:
            raise HTTPException(status_code=404, detail="해당 닉네임의 사용자를 찾을 수 없습니다")

        target_pk = int(user.id)
        wallet = ensure_wallet(db, user_pk=target_pk)
        db.refresh(wallet)

        now = _now()
        old_balance = int(wallet.balance)
        applied = int(points)
        new_balance = old_balance + applied
        if new_balance < 0:
            new_balance = 0
            applied = new_balance - old_balance
        if applied == 0:
            raise HTTPException(status_code=400, detail="차감할 잔액이 없습니다")

        wallet.balance = new_balance
        wallet.version = int(wallet.version) + 1
        wallet.updated_at = now

        if applied > 0:
            default_note = f"관리자 충전 → {nick}"
            message = f"{user.nickname}에게 {applied}P가 적립되었습니다"
        else:
            default_note = f"관리자 차감 → {nick}"
            message = f"{user.nickname}에서 {abs(applied)}P가 차감되었습니다"
            if applied != int(points):
                message += f" (요청 {abs(int(points))}P, 잔액 하한 0)"

        note = (memo or "").strip() or default_note
        db.add(
            PointTransaction(
                wallet_id=target_pk,
                type=TX_TYPE_ADJUST,
                amount=applied,
                balance_after=new_balance,
                ref_type=REF_TYPE_ADMIN,
                ref_id=int(admin_pk),
                idempotency_key=f"adjust:{uuid4().hex}",
                memo=note[:255],
                created_at=now,
            )
        )

        user.point = new_balance
        user.updated_at = now

        db.commit()
        return {
            "processed": True,
            "points": applied,
            "balance": new_balance,
            "nickname": user.nickname,
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


def create_charge(
    db: Session,
    *,
    user_pk: int,
    amount_krw: int,
) -> dict[str, object]:
    """payments(pending) 생성 후 FE 결제창용 paymentId 반환."""
    _require_portone_config()
    if amount_krw < MIN_CHARGE_KRW or amount_krw > MAX_CHARGE_KRW:
        raise HTTPException(
            status_code=400,
            detail=f"충전 금액은 {MIN_CHARGE_KRW}~{MAX_CHARGE_KRW}원입니다",
        )

    user = db.get(User, user_pk)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

    points_granted, bonus_points = points_for_amount_krw(amount_krw)
    if points_granted <= 0:
        raise HTTPException(status_code=400, detail="유효하지 않은 충전 금액입니다")

    ensure_wallet(db, user_pk=user_pk)

    payment_id = f"pay_{uuid4().hex}"
    now = _now()
    payment = Payment(
        user_id=user_pk,
        amount_krw=amount_krw,
        points_granted=points_granted,
        bonus_points=bonus_points,
        status=PAYMENT_STATUS_PENDING,
        pg_provider=PG_PROVIDER_PORTONE,
        pg_tid=None,
        idempotency_key=payment_id,
        paid_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    settings = get_settings()
    return {
        "payment_id": payment_id,
        "order_name": f"포인트 충전 {points_granted}P",
        "amount_krw": amount_krw,
        "points_granted": points_granted,
        "bonus_points": bonus_points,
        "store_id": settings.portone_store_id.strip(),
        "channel_key": settings.portone_channel_key.strip(),
        "status": payment.status,
        "customer_email": _buyer_email_for_pg(user),
        "customer_name": _buyer_name_for_pg(user),
    }


def _find_payment_by_payment_id(db: Session, payment_id: str) -> Payment | None:
    return db.scalar(
        select(Payment).where(Payment.idempotency_key == payment_id)
    )


def _complete_result(payment: Payment, *, balance: int, processed: bool, message: str) -> dict[str, object]:
    return {
        "processed": processed,
        "payment_id": payment.idempotency_key or "",
        "status": payment.status,
        "amount_krw": int(payment.amount_krw),
        "points_granted": int(payment.points_granted),
        "bonus_points": int(payment.bonus_points),
        "balance": balance,
        "message": message,
    }


def complete_charge(
    db: Session,
    *,
    payment_id: str,
    expect_user_pk: int | None = None,
) -> dict[str, object]:
    """
    포트원 결제 확인 후 포인트 적립 (멱등).

    expect_user_pk가 있으면 본인 주문만 허용 (클라이언트 complete).
    웹훅은 None.
    """
    payment_key = payment_id.strip()
    if not payment_key:
        raise HTTPException(status_code=400, detail="paymentId는 필수입니다")

    try:
        payment = _find_payment_by_payment_id(db, payment_key)
        if payment is None:
            raise HTTPException(status_code=404, detail="충전 주문을 찾을 수 없습니다")

        if expect_user_pk is not None and int(payment.user_id) != int(expect_user_pk):
            raise HTTPException(status_code=403, detail="본인 충전 주문만 완료할 수 있습니다")

        # 낙관적·동시성: 유저 행 잠금
        locked = db.execute(
            select(User.id).where(User.id == payment.user_id).with_for_update()
        ).scalar_one_or_none()
        if locked is None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        # 잠금 후 재조회
        db.refresh(payment)
        wallet = ensure_wallet(db, user_pk=int(payment.user_id))
        db.refresh(wallet)

        if payment.status == PAYMENT_STATUS_PAID:
            return _complete_result(
                payment,
                balance=int(wallet.balance),
                processed=False,
                message="이미 충전 완료된 주문입니다",
            )

        try:
            remote = portone_client.get_payment(payment_key)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="포트원 결제 조회에 실패했습니다",
            ) from exc

        if remote.status == "FAILED":
            payment.status = PAYMENT_STATUS_FAILED
            payment.updated_at = _now()
            db.commit()
            return _complete_result(
                payment,
                balance=int(wallet.balance),
                processed=False,
                message="결제가 실패했습니다",
            )

        if remote.status != "PAID":
            raise HTTPException(
                status_code=409,
                detail=f"아직 결제 완료 상태가 아닙니다 ({remote.status})",
            )

        if int(remote.amount_total) != int(payment.amount_krw):
            payment.status = PAYMENT_STATUS_FAILED
            payment.updated_at = _now()
            db.commit()
            raise HTTPException(status_code=400, detail="결제 금액이 주문과 일치하지 않습니다")

        # 이미 원장이 있으면 paid만 맞추고 종료
        tx_key = charge_idempotency_key(payment_key)
        existing_tx = db.scalar(
            select(PointTransaction).where(PointTransaction.idempotency_key == tx_key)
        )
        now = _now()
        if existing_tx is not None:
            payment.status = PAYMENT_STATUS_PAID
            payment.paid_at = payment.paid_at or now
            payment.pg_tid = remote.transaction_id or payment.pg_tid
            payment.updated_at = now
            db.commit()
            db.refresh(wallet)
            return _complete_result(
                payment,
                balance=int(wallet.balance),
                processed=False,
                message="이미 충전 완료된 주문입니다",
            )

        credit = int(payment.points_granted)
        new_balance = int(wallet.balance) + credit
        wallet.balance = new_balance
        wallet.version = int(wallet.version) + 1
        wallet.updated_at = now

        db.add(
            PointTransaction(
                wallet_id=int(payment.user_id),
                type=TX_TYPE_CHARGE,
                amount=credit,
                balance_after=new_balance,
                ref_type=REF_TYPE_PAYMENT,
                ref_id=int(payment.id),
                idempotency_key=tx_key,
                memo=f"포트원 충전 {payment_key}",
                created_at=now,
            )
        )

        payment.status = PAYMENT_STATUS_PAID
        payment.paid_at = now
        payment.pg_provider = PG_PROVIDER_PORTONE
        payment.pg_tid = remote.transaction_id
        payment.updated_at = now

        # users.point 캐시 동기화 (레거시 컬럼)
        user = db.get(User, int(payment.user_id))
        if user is not None:
            user.point = new_balance
            user.updated_at = now

        db.commit()
        return _complete_result(
            payment,
            balance=new_balance,
            processed=True,
            message="포인트 충전이 완료되었습니다",
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


def fail_charge(
    db: Session,
    *,
    payment_id: str,
    expect_user_pk: int,
) -> dict[str, object]:
    """위젯 실패·취소: pending → failed. 지갑은 변경하지 않음."""
    payment_key = payment_id.strip()
    if not payment_key:
        raise HTTPException(status_code=400, detail="paymentId는 필수입니다")

    try:
        payment = _find_payment_by_payment_id(db, payment_key)
        if payment is None:
            raise HTTPException(status_code=404, detail="충전 주문을 찾을 수 없습니다")
        if int(payment.user_id) != int(expect_user_pk):
            raise HTTPException(status_code=403, detail="본인 충전 주문만 실패 처리할 수 있습니다")

        if payment.status == PAYMENT_STATUS_PAID:
            raise HTTPException(status_code=409, detail="이미 충전 완료된 주문입니다")

        if payment.status == PAYMENT_STATUS_FAILED:
            return {
                "processed": False,
                "payment_id": payment.idempotency_key or payment_key,
                "status": payment.status,
                "message": "이미 실패로 기록된 주문입니다",
            }

        if payment.status != PAYMENT_STATUS_PENDING:
            raise HTTPException(
                status_code=409,
                detail=f"실패 처리할 수 없는 상태입니다 ({payment.status})",
            )

        payment.status = PAYMENT_STATUS_FAILED
        payment.updated_at = _now()
        db.commit()
        return {
            "processed": True,
            "payment_id": payment.idempotency_key or payment_key,
            "status": payment.status,
            "message": "결제 실패로 기록했습니다",
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


def list_charges(
    db: Session,
    *,
    user_pk: int,
    limit: int = 20,
) -> list[dict[str, object]]:
    """본인 충전 주문 내역. pending은 숨기고 paid/failed 등만 보여 준다."""
    limit = max(1, min(limit, 100))
    rows = db.scalars(
        select(Payment)
        .where(
            Payment.user_id == user_pk,
            Payment.status != PAYMENT_STATUS_PENDING,
        )
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": int(p.id),
            "payment_id": p.idempotency_key,
            "amount_krw": int(p.amount_krw),
            "points_granted": int(p.points_granted),
            "bonus_points": int(p.bonus_points),
            "status": p.status,
            "paid_at": p.paid_at,
            "created_at": p.created_at,
        }
        for p in rows
    ]


def handle_portone_webhook(
    db: Session,
    *,
    raw_body: str,
    headers: dict[str, str],
) -> dict[str, str]:
    """웹훅 검증 후 PAID면 적립. 검증 실패는 400."""
    try:
        webhook = portone_client.verify_webhook(raw_body, headers)
    except portone.webhook.WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail="웹훅 검증 실패") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payment_id = portone_client.extract_webhook_payment_id(webhook)
    if not payment_id:
        return {"status": "ignored"}

    # 결제 관련이면 complete 시도 (미결제면 409 → 웹훅은 200으로 흡수 가능)
    try:
        complete_charge(db, payment_id=payment_id, expect_user_pk=None)
    except HTTPException as exc:
        if exc.status_code in (404, 409):
            return {"status": "accepted", "detail": str(exc.detail)}
        raise
    return {"status": "ok"}
