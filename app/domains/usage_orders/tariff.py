# 충전기 출력(kW) → ev_operator_tariffs 단가 컬럼 매핑 (member만)
from __future__ import annotations

from decimal import Decimal
from typing import Any


# (최대 kW 상한, 컬럼명) — 작은 구간부터 매칭
_OUTPUT_RATE_BANDS: list[tuple[float, str]] = [
    (3.5, "rate_slow_3_5"),
    (7.0, "rate_slow_7"),
    (11.0, "rate_slow_11"),
    (14.0, "rate_mid_14"),
    (30.0, "rate_mid_30"),
    (50.0, "rate_fast_50"),
    (100.0, "rate_fast_100"),
    (200.0, "rate_ultra_200"),
    (350.0, "rate_ultra_350"),
]


def pick_member_rate_won(
    *,
    output_kw: float | None,
    tariff_row: Any,
) -> Decimal:
    """
    member 요금 행에서 출력대 단가(원/kWh)를 고른다.
    해당 밴드가 NULL이면 상위 밴드 → default_rate 순으로 폴백.
    """
    cols_in_order: list[str] = []
    if output_kw is not None and output_kw > 0:
        for upper, col in _OUTPUT_RATE_BANDS:
            if output_kw <= upper:
                cols_in_order.append(col)
                break
        else:
            cols_in_order.append("rate_ultra_350")
        # 선택 밴드 이후도 폴백 후보
        started = False
        for _, col in _OUTPUT_RATE_BANDS:
            if col == cols_in_order[0]:
                started = True
            if started and col not in cols_in_order:
                cols_in_order.append(col)
    else:
        cols_in_order = [c for _, c in _OUTPUT_RATE_BANDS]

    cols_in_order.append("default_rate")

    for col in cols_in_order:
        value = getattr(tariff_row, col, None)
        if value is None:
            continue
        rate = Decimal(str(value))
        if rate > 0:
            return rate

    raise ValueError("회원 요금 단가를 찾을 수 없습니다")
