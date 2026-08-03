"""
EV charger status collector (공공 data.go.kr → ev_charger_status upsert).

운영 주의 (합의):
- DATA_GO_KR_KEY 일 한도 공유 → PC·운영(Lightsail) **동시 수집 금지**
- 수집기는 서버 1프로세스(worker=1)만. uvicorn --reload / 다중 워커면 중복 호출
- PC 개발은 개인 DB + EV_STATUS_SYNC_ENABLED=false 권장
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.dialects.mysql import insert

from app.core.config import get_settings
from app.core.database import get_session_factory, is_db_configured
from app.domains.stations.models import EvChargerStatus

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
VALID_STATUS = frozenset({"1", "2", "3", "4", "5", "9"})

_scheduler: AsyncIOScheduler | None = None
_daily_calls = 0
_daily_calls_date: date | None = None
_sync_logging_configured = False


def _ensure_sync_logging() -> None:
    """status sync 로그에 KST 시각을 통일해 붙인다 (메시지별 datetime 금지)."""
    global _sync_logging_configured
    if _sync_logging_configured:
        return
    # uvicorn --reload 시 모듈만 재실행되고 Logger 인스턴스(handlers)는 유지됨
    for existing in logger.handlers:
        if getattr(existing, "_ev_status_sync", False):
            _sync_logging_configured = True
            return

    handler = logging.StreamHandler()
    handler._ev_status_sync = True  # type: ignore[attr-defined]
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [status-sync] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    formatter.converter = lambda secs: datetime.fromtimestamp(secs, KST).timetuple()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    _sync_logging_configured = True


_ensure_sync_logging()


def _today_kst() -> date:
    return datetime.now(KST).date()


def _reset_daily_counter_if_needed() -> None:
    global _daily_calls, _daily_calls_date
    today = _today_kst()
    if _daily_calls_date != today:
        _daily_calls = 0
        _daily_calls_date = today


def _can_call_outbound(limit: int) -> bool:
    _reset_daily_counter_if_needed()
    return _daily_calls < limit


def _record_outbound_call() -> None:
    global _daily_calls
    _reset_daily_counter_if_needed()
    _daily_calls += 1


def _status_endpoint(base_url: str) -> str:
    url = base_url.strip().rstrip("/")
    if url.endswith("getChargerStatus"):
        return url
    return f"{url}/getChargerStatus"


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    """data.go.kr JSON: body.items.item 이 list 또는 단일 dict."""
    if not isinstance(payload, dict):
        return []

    root = payload.get("response", payload)
    if not isinstance(root, dict):
        return []

    body = root.get("body", root)
    if not isinstance(body, dict):
        return []

    items = body.get("items")
    if items is None and isinstance(body.get("item"), (list, dict)):
        items = body
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    if not isinstance(items, dict):
        # 일부 응답은 items 가 곧 list 가 아니라 비어 있음
        return []

    item = items.get("item", items.get("items"))
    if item is None:
        return []
    if isinstance(item, dict):
        return [item]
    if isinstance(item, list):
        return [x for x in item if isinstance(x, dict)]
    return []


def _normalize_row(item: dict[str, Any]) -> dict[str, Any] | None:
    stat_id = item.get("statId") or item.get("stat_id")
    chger_id = item.get("chgerId") or item.get("chger_id")
    if not stat_id or not chger_id:
        return None

    raw_stat = item.get("stat")
    status = str(raw_stat).strip() if raw_stat is not None else ""
    charger_status = status if status in VALID_STATUS else None

    # output(kW)은 고정값 → ev_charger_info.output. status에는 상태만.
    return {
        "stat_id": str(stat_id),
        "chger_id": str(chger_id),
        "charger_status": charger_status,
        "last_updated": datetime.now(),
    }


def _filter_rows_in_info(
    db: Any, rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """ev_charger_status FK → ev_charger_info. info에 없는 쌍은 스킵."""
    from sqlalchemy import text

    if not rows:
        return [], 0

    pairs = {(r["stat_id"], r["chger_id"]) for r in rows}
    # (stat_id, chger_id) IN (...) — 청크 조회
    existing: set[tuple[str, str]] = set()
    pair_list = list(pairs)
    chunk_size = 500
    for i in range(0, len(pair_list), chunk_size):
        chunk = pair_list[i : i + chunk_size]
        placeholders = ", ".join(
            f"(:s{j}, :c{j})" for j in range(len(chunk))
        )
        params: dict[str, str] = {}
        for j, (sid, cid) in enumerate(chunk):
            params[f"s{j}"] = sid
            params[f"c{j}"] = cid
        result = db.execute(
            text(
                f"SELECT stat_id, chger_id FROM ev_charger_info "
                f"WHERE (stat_id, chger_id) IN ({placeholders})"
            ),
            params,
        )
        existing.update((str(a), str(b)) for a, b in result.all())

    kept = [
        r for r in rows if (r["stat_id"], r["chger_id"]) in existing
    ]
    return kept, len(rows) - len(kept)


def _upsert_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    db = get_session_factory()()
    try:
        rows, skipped = _filter_rows_in_info(db, rows)
        if skipped:
            logger.warning(
                "status sync: info에 없어 FK 스킵 %s건 (유지 %s건)",
                skipped,
                len(rows),
            )
        if not rows:
            return 0

        # MySQL 다중 VALUES + ON DUPLICATE KEY UPDATE
        chunk_size = 500
        written = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = insert(EvChargerStatus).values(chunk)
            stmt = stmt.on_duplicate_key_update(
                charger_status=stmt.inserted.charger_status,
                last_updated=stmt.inserted.last_updated,
            )
            db.execute(stmt)
            written += len(chunk)
        db.commit()
        return written
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def collect_charger_status() -> None:
    settings = get_settings()
    base = (settings.ev_charger_api_url or "").strip()
    key = (settings.data_go_kr_key or "").strip()

    if not base or not key:
        logger.warning(
            "status sync skip: EV_CHARGER_API_URL / DATA_GO_KR_KEY 미설정"
        )
        return

    if not is_db_configured():
        logger.warning("status sync skip: DB 미설정")
        return

    limit = settings.ev_status_daily_call_limit
    if not _can_call_outbound(limit):
        logger.error(
            "status sync skip: 일일 outbound 한도 초과 "
            "(date=%s calls=%s limit=%s). "
            "PC·운영 동시 수집 여부·키 공유를 확인하세요.",
            _today_kst().isoformat(),
            _daily_calls,
            limit,
        )
        return

    url = _status_endpoint(base)
    params = {
        "ServiceKey": key,
        "pageNo": 1,
        "numOfRows": settings.ev_status_num_of_rows,
        "period": settings.ev_status_period_minutes,
        "dataType": "JSON",
    }
    if settings.ev_status_zcode:
        params["zcode"] = settings.ev_status_zcode

    _record_outbound_call()
    logger.info(
        "status sync call #%s/%s → %s (zcode=%s period=%s)",
        _daily_calls,
        limit,
        url,
        settings.ev_status_zcode or "-",
        settings.ev_status_period_minutes,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # serviceKey 가 이미 URL-encoded 인 경우가 있어 재인코딩 방지
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.exception(
            "status sync HTTP %s — 당일 한도(429)일 수 있음",
            exc.response.status_code,
        )
        return
    except Exception:
        logger.exception("status sync API 호출 실패")
        return

    raw_items = _extract_items(payload)
    rows = [r for r in (_normalize_row(it) for it in raw_items) if r]
    if not rows:
        logger.warning(
            "status sync: 파싱된 item 0건 (원본 items=%s). "
            "응답 형식·serviceKey·엔드포인트를 확인하세요.",
            len(raw_items),
        )
        return

    try:
        written = await asyncio.to_thread(_upsert_rows, rows)
    except Exception:
        logger.exception("status sync DB upsert 실패")
        return

    logger.info("status sync upsert ok: %s rows", written)


async def _scheduled_collect() -> None:
    await collect_charger_status()


def _log_startup_warnings(*, enabled: bool) -> None:
    settings = get_settings()
    logger.warning(
        "=== EV status sync 주의 === "
        "DATA_GO_KR_KEY 일 한도 공유. "
        "PC와 운영(Lightsail)에서 동시에 EV_STATUS_SYNC_ENABLED=true 금지. "
        "운영 반영 후 PC는 개인 DB + sync OFF로 작업. "
        "uvicorn --reload / workers>1 이면 수집이 중복될 수 있음. "
        "enabled=%s app_env=%s daily_limit=%s",
        enabled,
        settings.app_env,
        settings.ev_status_daily_call_limit,
    )


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    enabled = bool(settings.ev_status_sync_enabled)
    _log_startup_warnings(enabled=enabled)

    if not enabled:
        logger.info(
            "status sync scheduler OFF "
            "(EV_STATUS_SYNC_ENABLED=true 로 켜세요)"
        )
        return

    if _scheduler is not None and _scheduler.running:
        logger.warning("status sync scheduler already running — skip start")
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _scheduled_collect,
        trigger="interval",
        minutes=settings.ev_status_interval_minutes,
        id="ev_charger_status_collect",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "status sync scheduler ON (every %s min)",
        settings.ev_status_interval_minutes,
    )

    # 기동 직후 1회 (실패해도 API 서버는 유지)
    try:
        _scheduler.add_job(
            _scheduled_collect,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=3),
            id="ev_charger_status_collect_once",
            replace_existing=True,
        )
    except Exception:
        logger.exception("status sync immediate job schedule failed")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("status sync scheduler stopped")
    _scheduler = None
