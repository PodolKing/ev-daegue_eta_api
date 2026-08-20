# usage_orders 상태·충전기 상태·요금 상수
# DB CHECK: status ∈ draft|confirmed|cancelled|refunded
# DB CHECK: kwh_source ∈ manual|preset|operator_session
# DB CHECK: kwh > 0 AND kwh <= 400

STATUS_DRAFT = "draft"
STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"
STATUS_REFUNDED = "refunded"

CHARGER_STATUS_WAIT = "2"  # 충전 대기
CHARGER_STATUS_CHARGING = "3"  # 충전 중

MEMBER_TYPE = "member"
TARIFF_FALLBACK_BUSI_ID = "__AVG__"

KWH_SOURCE_PRESET = "preset"  # 가결제 시점 placeholder
KWH_SOURCE_MANUAL = "manual"  # 충전 완료 시 실측/입력

TX_TYPE_USE = "use"
TX_TYPE_REFUND = "refund"
REF_TYPE_USAGE_ORDER = "usage_order"

MIN_HOLD_KRW = 1_000
MAX_HOLD_KRW = 1_000_000

# DB ck_usage_orders_kwh: (0, 400]
PLACEHOLDER_KWH = "0.01"
MIN_KWH = 0.01
MAX_KWH = 400.0

PAY_MODE_AMOUNT = "amount"
PAY_MODE_USAGE = "usage"