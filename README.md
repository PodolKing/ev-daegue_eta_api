# EV SafeCharge · API

**대구 EV 세이프차지** Backend — 충전소 실데이터 조회, 가용 집계, (진행 중) 인증·포인트까지 담당하는 **FastAPI** 서비스.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.13x-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)

## Why this API

프론트는 지도만 그립니다. **좌표·반경·가용 대수**는 이 API가 DB에서 집계해 제공합니다.

- 충전소 단위(`stat_id`) 집계
- `availableCount`: 상태 코드 `2`(충전대기)만 카운트 — **null ≠ 0**
- 목록 거리: DB 위경도 **Haversine**(+ bbox). TMAP 경로거리와 분리
- 전량(~수만 건) 응답 금지 → 현위치 반경 + limit

## Highlights

- OpenAPI 자동 문서 (`/docs`)
- 응답 필드 **camelCase** 통일
- Domain 폴더 구조: `stations`(활성) · `auth` / `points`(1개월 토이) · recommendations·traffic 등 스켈레톤
- TMAP **서버 키**는 ETA·길찾기 등 서버 전용 (목록 거리 계산용 아님)
- MariaDB/MySQL + SQLAlchemy (`mysql+pymysql://…`, `DB_*` 조립)

## Roadmap (1개월 토이 스코프)

| 주차 | 목표 |
|---|---|
| 1주차 | DB 연결, `/health`, 로그인 제공자 1종 확정 + `me` API |
| 2주차 | stations 실조회(반경·집계·null 규칙), `point_wallets` 잔액 조회 |
| 3주차 | 포인트 충전 플로우(테스트 충전 또는 PG 테스트) + ledger 내역 |
| 4주차 | 통합 QA, README·`.env.example` 정리, 데모 시나리오 |

> 팀 합의사항(2026-07-23/24) 기준 로드맵입니다. 초기 기획서의 Express/Prisma/ML 추천 스택은 이번 1개월 범위에는 포함되지 않으며, 필요 시 팀 재합의 후 진행합니다.

## Tech stack

| Area | Choice |
|---|---|
| Runtime | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 |
| DB | MariaDB / MySQL |
| Validation | Pydantic v2 (`CamelModel`) |
| Maps (server) | TMAP REST (`TMAP_APP_KEY`) — ETA/routing |

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
| `GET /api/v1/stations` | Nearby stations (see `docs/stations_api.md`) |

## Configuration (names only)

| Variable | Role |
|---|---|
| `DB_HOST` `DB_PORT` `DB_USER` `DB_PASSWORD` `DB_NAME` | Assembled into SQLAlchemy URL |
| `DATABASE_URL` | Optional override |
| `TMAP_APP_KEY` | Server-only routing/ETA |
| `CORS_ORIGINS` | Allowed FE origins |
| `DATA_GO_KR_KEY` | External data / collection (as needed) |

Never commit `.env`. Use `.env.example` for key names only.

## Project layout

```text
app/
  core/           config, database
  schemas/        CamelModel
  domains/
    stations/     primary path
    auth/         skeleton (OAuth TBD)
    points/       skeleton (wallet / ledger)
    …             recommendations, traffic, …
docs/
  stations_api.md
  rules/
```

## Current status

- 완료: FastAPI + SQLAlchemy 뼈대, stations 라우트 시그니처, camelCase 응답 규칙, DB env 조립
- 진행 중: stations DB 조회 서비스 구현
- 예정: 로그인 1종(OAuth) + `me`, 포인트 지갑/충전/ledger API

## Related

- Frontend repo: `web` (Next.js · TMAP map UI)
- Contract: `docs/stations_api.md`
- Team conventions: `docs/rules/`

## License / notice

팀 프로젝트·학습용 초안입니다. 상용 PG 정산·멀티 소셜·ML 예측은 범위 밖이며, 포인트는 테스트 충전(A안) 또는 PG 테스트(B안)로 데모합니다.