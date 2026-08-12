# 포인트 충전 규칙·상태 상수

# 1원 = 1포인트 (보너스 없음). 금액은 서버에서만 확정한다.
KRW_PER_POINT = 1

MIN_CHARGE_KRW = 1_000
MAX_CHARGE_KRW = 1_000_000

PG_PROVIDER_PORTONE = "portone"

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_CANCELLED = "cancelled"
PAYMENT_STATUS_REFUNDED = "refunded"

TX_TYPE_CHARGE = "charge"
TX_TYPE_ADJUST = "adjust"
REF_TYPE_PAYMENT = "payment"
REF_TYPE_ADMIN = "admin"

# 포트원 없이 직접 적립 한도
MIN_DIRECT_POINTS = 1
MAX_DIRECT_POINTS = 1_000_000


def points_for_amount_krw(amount_krw: int) -> tuple[int, int]:
    """(points_granted, bonus_points). 현재는 1:1, 보너스 0."""
    points = amount_krw // KRW_PER_POINT
    return points, 0


def charge_idempotency_key(payment_id: str) -> str:
    """point_transactions 중복 적립 방지 키."""
    return f"charge:{payment_id}"
