# EV SafeCharge 백엔드 작업 가이드 (FastAPI)

> 대상: 백엔드 담당  
> 기술 스택: **Python 3.11+ · FastAPI · Uvicorn · SQLAlchemy 2 · Pydantic v2 · MariaDB/MySQL (PyMySQL)**  
> 원본: `docs/02_BACKEND_GUIDE.md`(Express + TypeScript + Prisma) → FastAPI 프로젝트에 맞게 재작성  
> 응답 필드: **camelCase** (`CamelModel`)

## 1. 이번 작업의 목표

백엔드의 첫 번째 목표는 모든 외부 API를 한 번에 연결하는 것이 아닙니다.

**프론트가 쓸 수 있는 충전소·인증·(진행 중) 포인트 API를 계약에 맞게 제공하고, DB·수집·외부 연동은 도메인 service 내부에서 교체 가능하게 유지하는 것**이 목표입니다.

```text
.env / DB / (선택) 목·시드
→ domains/*/service.py
→ controller.py (조립·응답 변환)
→ router.py (경로·Depends)
→ camelCase JSON
→ /docs(OpenAPI)로 FE·Postman 확인
```

현재 이 리포의 우선 경로:

| 도메인 | 상태 |
|---|---|
| `stations` | 반경 목록·Haversine·가용 집계 (실DB 방향) |
| `auth` | 로컬 회원가입·로그인·JWT·`/me` (카카오 OAuth는 이후) |
| `places` | TMAP POI 프록시 |
| `points` 등 | 스켈레톤 |

## 2. 참고해야 하는 파일

| 파일 | 용도 |
|---|---|
| `docs/stations_api.md` | `GET /api/v1/stations` 계약 |
| `docs/teamdeveloper.md` | 팀 실행·합의·온보딩 |
| `docs/규칙.md` | `requirements.txt` 충돌 방지 |
| `.env.example` | env 키 이름만 |
| `app/schemas/base.py` | `CamelModel` |
| `app/core/config.py` | Settings / DB URL / JWT |
| `app/core/database.py` | Engine·Session·`get_db` |
| `app/main.py` | 앱·CORS·라우터 등록 |
| `README.md` | Quick start·스택 |

## 3. 권장 폴더 구조 (현재 리포)

```text
app/
├─ main.py                 # FastAPI 앱, CORS, include_router
├─ core/
│  ├─ config.py            # pydantic-settings
│  └─ database.py          # SQLAlchemy engine / get_db
├─ schemas/
│  └─ base.py              # CamelModel
└─ domains/
   ├─ stations/
   │  ├─ router.py
   │  ├─ controller.py
   │  ├─ service.py
   │  ├─ models.py
   │  └─ schema.py
   ├─ auth/
   │  ├─ router.py
   │  ├─ controller.py
   │  ├─ service.py
   │  ├─ models.py
   │  ├─ schema.py
   │  └─ deps.py           # JWT Bearer Depends
   ├─ places/
   ├─ points/
   └─ …                    # recommendations, traffic, …
docs/
├─ stations_api.md
├─ teamdeveloper.md
├─ 규칙.md
└─ BACKEND_GUILD.md        # 본 문서
```

계층 최소 규칙:

- 라우터에 DB·비즈니스 로직을 몰아넣지 않는다.
- 권장: `router → controller → service` (`stations` / `auth`와 동일).
- 엔드포인트가 매우 작으면 `router → service`만으로도 가능하나, 팀 컨벤션은 controller 분리를 우선한다.

## 4. 로컬 실행

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env

.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# 같은 Wi‑Fi 폰 테스트 시
# .\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| 확인 | URL |
|---|---|
| Health | http://localhost:8000/health |
| OpenAPI | http://localhost:8000/docs |

## 5. 작업 순서 (FastAPI 기준)

### 1단계: 서버 실행과 헬스체크

```http
GET /health
```

예시 응답:

```json
{
  "status": "ok",
  "env": "development"
}
```

완료 조건:

- uvicorn 기동 성공
- `/health` 200
- `/docs`에서 스키마 확인 가능

### 2단계: 충전소 근처 목록 API

계약: `docs/stations_api.md`

```http
GET /api/v1/stations?lat=35.8714&lng=128.6014&radiusKm=3&limit=50
```

구현 위치:

- `app/domains/stations/router.py`
- `app/domains/stations/controller.py`
- `app/domains/stations/service.py`
- `app/domains/stations/models.py` (`ev_charger_info` / `ev_charger_status`)

규칙 요약:

- `stat_id` 단위 집계
- `availableCount`: 상태 `'2'`만 카운트, 관측 없으면 **null** (0과 구분)
- 거리: DB Haversine (+ bbox). TMAP 경로거리와 분리
- 전량 dump 금지 → 반경 + `limit`

service 스케치:

```python
def list_stations_near(db: Session, *, lat: float, lng: float, radius_km: float, limit: int) -> list[dict]:
    # bbox → Haversine → group by stat_id → status LEFT JOIN → sort → limit
    ...
```

router는 Query/`Depends(get_db)`만 두고 controller를 호출한다.

### 3단계: 목록 쿼리·클램프

| 쿼리 | 기본 | 상한 | 비고 |
|---|---|---|---|
| `lat` / `lng` | 필수 | — | 현위치 |
| `radiusKm` | `3` | `10` | 직선 반경(km) |
| `limit` | `50` | `100` | 충전소 개수 |

잘못된 값은 FastAPI/`Query(ge=…, le=…)` 또는 service clamp로 처리한다.

### 4단계: 충전소 상세 (필요 시)

초기 가이드의 `:stationId` 상세가 있었다면, 이 리포에서는 목록이 1차 계약이다.  
상세를 추가할 때:

```http
GET /api/v1/stations/{stationId}
```

- 스키마·라우터를 `stations` 도메인에 추가
- 없으면 `HTTPException(status_code=404, detail="…")`

### 5단계: 추천 API (스켈레톤 → 실로직)

```http
GET /api/v1/recommendations
```

현재는 스켈레톤일 수 있다. 목/규칙 엔진이 준비되면 `domains/recommendations/service.py` 내부만 교체한다.

선택 쿼리 예: `lat`, `lng`, `radiusKm`

### 6단계: 인증 (로컬 계정)

구현 위치: `app/domains/auth/`

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/api/v1/auth/signup` | 회원가입 (bcrypt) |
| `POST` | `/api/v1/auth/login` | 로그인 → JWT |
| `GET` | `/api/v1/auth/me` | Bearer 토큰 → 현재 유저 |
| `POST` | `/api/v1/auth/logout` | 클라이언트 토큰 삭제 안내 |

요청 예 (signup):

```json
{
  "userId": "testuser01",
  "password": "password123",
  "nickname": "테스터",
  "address": "대구광역시 중구",
  "detailAddress": "101동 202호"
}
```

- 테이블: `users` (`models.py`)
- JWT: `.env`의 `JWT_SECRET` 등
- 카카오 OAuth: 이후 단계 (env 키 이름만 `.env.example`에 예약)

Depends 예:

```python
from app.domains.auth.deps import get_current_user, get_current_user_optional
```

### 7단계: 오류·응답 규칙

FastAPI에서는 `HTTPException`이 기본이다.

```python
raise HTTPException(status_code=400, detail="이미 가입된 userId 존재")
```

팀에서 공통 envelope가 필요하면 나중에 통일한다. 당분간:

| 상태 | 상황 예 |
|---|---|
| 400 | 검증·중복·로그인 실패 |
| 401 | JWT 없음/무효 (`get_current_user`) |
| 403 | 비활성 계정 등 |
| 404 | 리소스 없음 |
| 503 | DB 미설정 |
| 500 | 예상치 못한 서버 오류 (내부 예외 객체는 클라이언트에 노출하지 않음) |

비밀번호·시크릿은 로그·응답에 넣지 않는다.

### 8단계: CORS와 환경변수

`.env.example` 키 이름만 참고한다. 실값은 커밋하지 않는다.

| 키 | 용도 |
|---|---|
| `DB_HOST` `DB_PORT` `DB_USER` `DB_PASSWORD` `DB_NAME` | SQLAlchemy URL 조립 |
| `DATABASE_URL` | (선택) 있으면 우선 |
| `CORS_ORIGINS` | FE origin (쉼표 구분) |
| `TMAP_APP_KEY` | 서버 전용 POI/ETA |
| `JWT_SECRET` `JWT_ALGORITHM` `JWT_EXPIRE_MINUTES` | 로컬 로그인 JWT |
| `DATA_GO_KR_KEY` | 수집·연동 시 |

`config.py`는 `pydantic-settings`로 `.env`를 읽는다.

### 9단계: 공공데이터 → API 변환

원본 필드명을 프론트에 그대로 보내지 않는다. service 또는 mapper에서 camelCase 계약 필드로 변환한다.

예 (개념):

```python
def to_station_item(row: Mapping) -> dict:
    return {
        "station_id": row["stat_id"],
        "name": row["stat_nm"],
        "address": row["addr"],
        "lat": float(row["lat"]),
        "lng": float(row["lng"]),
        "available_count": ...,  # 응답 시 availableCount
        "distance_km": ...,
        "charger_total": ...,
        "source_mode": "LIVE",
    }
```

상태코드 `'2'` = 충전대기만 `availableCount`에 합산. 관측 없으면 `null`.

### 10단계: DB 매핑 (이 리포 기준)

충전소 실데이터는 대략:

```text
ev_charger_info     # 충전기/충전소 정적 정보 (복합키 stat_id + chger_id)
ev_charger_status   # 상태 (동일 키)
```

회원:

```text
users  # user_id, password(hash), nickname, address, detail_address, role, ...
```

ORM: SQLAlchemy `models.py`가 테이블에 맞춘다. Prisma migrate 대신 **기존 MariaDB 스키마에 매핑**하는 방식이 기본이다.

### 11단계: 의존성

- 패키지 추가 시 `docs/규칙.md`를 따른다 (`requirements.txt` **맨 아래 append**, `==` 고정, A-Z 재정렬 금지, 충돌 마커 금지).
- `pip freeze`로 파일 전체를 덮어쓰지 말고 변경분만 반영한다.

## 6. GitHub 이슈 분리 예시

### BE-01 서버·헬스

- uvicorn 실행
- `GET /health`
- `/docs` 확인

### BE-02 stations 목록

- `GET /api/v1/stations`
- Haversine·집계·`availableCount` null 규칙
- `docs/stations_api.md`와 일치

### BE-03 auth 로컬

- signup / login / me / logout
- bcrypt + JWT
- `users` 테이블 매핑

### BE-04 places / TMAP

- `TMAP_APP_KEY` 서버 전용
- FE 지도 키와 이름 분리

### BE-05 points (로드맵)

- wallet 잔액·충전·ledger (팀 합의 후)

## 7. API 테스트 체크리스트

- [ ] `GET /health` → 200
- [ ] `GET /docs`에 stations·auth 등 노출
- [ ] `GET /api/v1/stations?lat=&lng=` → `items` 배열, camelCase
- [ ] `availableCount`가 null일 수 있음 (0과 구분)
- [ ] `POST /api/v1/auth/signup` → password 미포함 응답
- [ ] `POST /api/v1/auth/login` → `accessToken`
- [ ] `GET /api/v1/auth/me` + Bearer → user 또는 null
- [ ] CORS: `CORS_ORIGINS`에 FE 포함
- [ ] `.env` 미커밋

Postman 회원가입 예:

```http
POST http://localhost:8000/api/v1/auth/signup
Content-Type: application/json
```

## 8. 1차 완료 기준 (이 리포에 맞춤)

- [ ] FastAPI 서버가 안정적으로 기동된다.
- [ ] stations 목록 계약(`stations_api.md`)을 만족한다.
- [ ] auth 로컬 가입·로그인이 동작한다.
- [ ] 응답이 camelCase로 통일된다.
- [ ] DB·JWT 키는 `.env`에만 있다.
- [ ] OpenAPI(`/docs`)로 FE가 계약을 확인할 수 있다.

## 9. 데이터·FE에 요청할 내용

- 충전기 상태코드 매핑 (특히 `'2'` 충전대기)
- `stat_id` / `chger_id` 정의
- 결측 lat/lng·status 처리
- FE `NEXT_PUBLIC_API_BASE_URL` ↔ BE `CORS_ORIGINS`
- 지도 키(`NEXT_PUBLIC_TMAP_MAP_KEY`) vs 서버 키(`TMAP_APP_KEY`) 분리

## 10. 지금 무리해서 하지 않아도 되는 것

- 카카오·Google·네이버 OAuth 동시 완성
- 전체 외부 API 일괄 연동
- 대규모 캐시·운영 모니터링
- AI 추천 모델 학습
- Express/Prisma로의 재이전

먼저 **고정된 API 계약 + FE 연결 + stations/auth 안정화**를 목표로 한다.

## 11. Express 가이드와의 대응표

| Express + Prisma 가이드 | FastAPI 이 리포 |
|---|---|
| `routes/*.ts` | `domains/*/router.py` |
| `controllers/*.ts` | `domains/*/controller.py` |
| `services/*.ts` | `domains/*/service.py` |
| Prisma Client | SQLAlchemy `Session` + `models.py` |
| `res.json` / zod | Pydantic schema + `CamelModel` |
| `PORT=4000` | uvicorn `--port 8000` |
| `DATA_MODE=mock` | DB 미설정 시 빈 목록 등 (도메인별) |
| Swagger 수동 | FastAPI `/docs` 자동 |

`02_BACKEND_GUIDE.md`는 초기 Express 가정용으로 남겨 두고, **일상 작업은 본 문서(`BACKEND_GUILD.md`)를 따른다.**
