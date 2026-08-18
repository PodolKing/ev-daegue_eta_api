# EV SafeCharge · API

**대구 EV 세이프차지** Backend — 충전소 실조회, 인증, 포인트, 이용 결제 데모를 제공하는 **FastAPI** 서비스입니다.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.13x-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)

프론트는 지도를 그립니다. **좌표·반경·가용 대수·계정·결제 장부**는 이 API가 DB와 외부 연동으로 맡습니다.

충전소는 `stat_id` 단위로 집계하고, `availableCount`는 상태 코드 `2`(충전대기)만 셉니다. **null ≠ 0**입니다. 목록 거리는 DB 위경도 Haversine(+ bbox)이며 TMAP 경로 거리와 분리됩니다. 전량 응답은 하지 않고 현위치 반경 + limit만 줍니다.

## 이 API가 맡는 일

- **충전소**: 반경 조회·검색, 공공 충전기 status **수집·읽기**(앱이 status를 쓰지 않음)
- **인증**: 로컬 가입/로그인, 카카오·구글·네이버, JWT · `GET /auth/me`
- **멤버십**: 즐겨찾기, 내 차량, 장소 검색(TMAP POI), 경로/ETA
- **포인트**: PortOne 원→P 충전, 잔액·내역. ADMIN만 `/credit`으로 지갑 ± 조절
- **이용 결제(데모)**: `usage_orders` 요청→가결제→완료→포인트 차감. 실패 시 cancel. 공공 status와 무관
- **추천**: 외부 추천 모델 서버 프록시

OpenAPI는 `/docs`입니다. 응답은 **camelCase**입니다. 정본 경로는 각 도메인 `router.py`입니다.

데모 API는 동작합니다. 예약, 날씨, 상용 PG 정산, PortOne 콘솔 취소↔앱 포인트 자동 회수는 범위 밖입니다.

## Tech stack

| Area | Choice |
|---|---|
| Runtime | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 |
| DB | MariaDB (local) / Postgres (Supabase) — `DB_BACKEND` |
| Validation | Pydantic v2 (`CamelModel`) |
| Auth | JWT, OAuth (Authlib) |
| Payments | PortOne server SDK |
| Maps (server) | TMAP REST (`TMAP_APP_KEY`) — POI·ETA. 목록 거리 계산용이 아님 |
| Jobs | APScheduler (충전기 status 수집, 호스트당 1대만 활성) |

## Quick start

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env

.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness |
| `GET /docs` | OpenAPI UI |
| `GET /api/v1/stations` | Nearby stations (`docs/stations_api.md`) |

## Tests

```bash
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest tests -q
```

외부 네트워크(PortOne·소셜·TMAP·추천 서버)는 어떤 레벨에서도 호출하지 않습니다. DB는 두 가지를 씁니다:

- **서비스·라우터 계층**(`tests/test_*.py`, 43개): SQLite in-memory. `test_auth.py` 등은 도메인 서비스 함수를 직접 호출하고, `test_routers.py`는 `TestClient`로 실제 HTTP 요청을 보내 라우팅·Pydantic 검증·JWT 인증 체인·camelCase 직렬화까지 검증합니다.
- **실DB 통합 계층**(`tests/integration/`, 8개): 진짜 MySQL 8.0 컨테이너. `stations`의 반경 조회(raw SQL, `JSON_ARRAYAGG` 등 MySQL 전용 문법)와 `SELECT ... FOR UPDATE` 동시성 잠금은 SQLite로는 애초에 실행이 안 되기 때문에 별도로 붙였습니다.

```bash
docker run -d --name ev-test-mysql \
  -e MYSQL_ROOT_PASSWORD=test -e MYSQL_DATABASE=ev_test \
  -p 3307:3306 mysql:8.0
```

이 컨테이너가 없으면 `tests/integration/`의 8개만 `SKIPPED`로 표시되고 나머지 43개는 그대로 통과합니다 — Docker가 필수는 아닙니다.

요구사항 ID(`FR-xxx`) ↔ 테스트 매핑, 커버리지 범위·경계는 `../대구_EV_세이프차지_종합_요구사항_정의서_v2.0.md` §14~15와 `../대구_EV_세이프차지_테스트_계획서_v1.0.md` 참고.

## Configuration (names only)

| Variable | Role |
|---|---|
| `DB_BACKEND` | `local` (MariaDB) or `supabase` (Postgres) |
| `DB_HOST` `DB_PORT` `DB_USER` `DB_PASSWORD` `DB_NAME` | Local MariaDB (`DB_BACKEND=local`) |
| `SUPABASE_DB_URL` | Supabase Postgres URI (`DB_BACKEND=supabase`) |
| `DATABASE_URL` | Optional full override |
| `CORS_ORIGINS` | Allowed FE origins |
| `FRONTEND_ORIGIN` | OAuth 콜백 후 FE origin |
| `TMAP_APP_KEY` | Server-only POI / routing / ETA |
| `DATA_GO_KR_KEY` | 공공 충전기 수집 |
| `EV_STATUS_SYNC_ENABLED` | status 수집 on/off (한 호스트만 true) |
| `JWT_SECRET` | Local JWT |
| `PORTONE_*` | Point charge (names — `.env.example`) |
| `RECOMMEND_API_BASE_URL` | External recommend model server |
| `RECOMMEND_API_TIMEOUT` | Recommend HTTP timeout (seconds) |
| `RECOMMEND_API_KEY` | Recommend `X-API-Key` (local `.env` only) |

실값은 커밋하지 않습니다. `.env.example`만 키 이름용입니다.

## Project layout

```text
app/
  core/           config, database
  schemas/        CamelModel
  domains/
    stations/     nearby + search + status sync
    auth/         signup, login, me, OAuth
    points/       balance, PortOne, ADMIN credit
    usage_orders/ demo settlement
    favorites/ cars/ places/ routes/ recommendations/
docs/
  stations_api.md
  teamdeveloper.md
```

## Related

- Frontend: `web` (Next.js · TMAP)
- Contract: `docs/stations_api.md`
- Team log: `docs/teamdeveloper.md`

## License / notice

팀 프로젝트·학습용 초안입니다. 상용 정산·예약·공공 충전기 상태 쓰기는 범위 밖입니다.
