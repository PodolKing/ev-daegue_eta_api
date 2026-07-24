# Team Developer Log

> 팀·에이전트 공통 개발 기록 + **로컬 실행·세팅 안내**.  
> **시크릿·실키·비밀번호·개인정보·내부 전용 호스트/계정 실값은 적지 않는다.**  
> Git 반영 위치: `web/docs/teamdeveloper.md`, `api/docs/teamdeveloper.md` (워크스페이스 `docs/`와 동기화)

---

## 팀원 온보딩 — 실행·세팅 (민감정보 없음)

### 0. 전제
| 항목 | 내용 |
|---|---|
| 워크스페이스 | 상위 `ev-daegue_eta/` — **git 없음** (로컬에서 FE+BE 같이 열기용) |
| Frontend 리포 | `web/` — 별도 git |
| Backend 리포 | `api/` — 별도 git |
| Node | 권장 20+ (로컬에서 24.x 사용 가능) |
| Python | 권장 3.11+ |
| DB | MariaDB/MySQL (stations 실조회 시). 스켈레톤만이면 DB 없이도 `/health`·빈 stations 가능 |

### 1. 세팅 순서 (권장)

1. 리포 clone (또는 워크스페이스에서 `web/`, `api/` 확인)
2. **Backend** 세팅 → 서버 기동 확인 (`/health`)
3. **Frontend** 세팅 → `npm run dev` → 지도(`/map`) 확인
4. (선택) DB 계정·TMAP·OAuth 키는 **각자 로컬 `.env`에만** 입력 (커밋 금지)

### 2. Backend (`api/`)

```bash
cd api
python -m venv .venv

# Windows
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env

# macOS / Linux
# source .venv/bin/activate
# pip install -r requirements.txt
# cp .env.example .env

.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

| 확인 | URL |
|---|---|
| Health | http://localhost:8000/health |
| OpenAPI | http://localhost:8000/docs |

**`.env`에 채울 키 이름만** (값은 본인 PC / 팀 시크릿 채널로):

| 키 | 용도 |
|---|---|
| `DB_HOST` `DB_PORT` `DB_USER` `DB_PASSWORD` `DB_NAME` | DB. 내부에서 `mysql+pymysql://…` 조립 |
| `DATABASE_URL` | (선택) 있으면 DB_*보다 우선 |
| `CORS_ORIGINS` | FE 주소. 로컬 기본 예: `http://localhost:3000` |
| `TMAP_APP_KEY` | **서버 전용** POI/장소검색·ETA/길찾기 (목록 거리 계산용 아님) |
| `DATA_GO_KR_KEY` | 수집·연동 시 |
| `JWT_SECRET` / `KAKAO_CLIENT_*` 등 | Auth 구현 시 (example 주석 참고) |

`.env`는 **커밋하지 않음**. `.env.example`만 리포에 둠.

### 3. Frontend (`web/`)

```bash
cd web
npm install
copy .env.example .env.local   # macOS/Linux: cp .env.example .env.local

npm run dev
```

| 확인 | URL |
|---|---|
| 앱 | http://localhost:3000 → `/map`으로 이동 |
| 로그인 UI | http://localhost:3000/login |
| 회원가입 UI | http://localhost:3000/signup |

**`.env.local` 키 이름만:**

| 키 | 용도 |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | BE base (로컬 예: `http://localhost:8000`, trailing slash 없이) |
| `NEXT_PUBLIC_TMAP_MAP_KEY` | **지도 SDK 전용** (브라우저 노출). BE `TMAP_APP_KEY`(POI/ETA REST)와 **이름·용도 분리** |

DB 비밀번호·서버 REST 키를 FE env에 넣지 않는다.

### 4. 일상 실행 (두 터미널)

```text
터미널 A:  cd api  →  uvicorn … --port 8000
터미널 B:  cd web  →  npm run dev
```

브라우저: `http://localhost:3000/map`  
API 문서: `http://localhost:8000/docs`

### 5. 주요 경로·문서

| 구분 | 경로 |
|---|---|
| FE 지도 | `/map` |
| FE 로그인/가입 | `/login`, `/signup` |
| stations 계약 | `api/docs/stations_api.md` |
| auth 계약 | `api/docs/auth_api.md` |
| FE auth 요약 | `web/docs/auth_ux.md` |
| 팀 규칙 | `docs/rules/` (각 리포 `docs/rules/` 동기본) |
| Cursor 규칙 | `.cursor/rules/` (BE 수정 시 사전 허락 등) |

### 6. 자주 막히는 것 (로컬)

| 증상 | 대처 |
|---|---|
| `Turbopack` / SWC `Application Control policy has blocked` | 프로젝트(또는 `node_modules`)를 제외 폴더에 등록 후 터미널 재실행. 정상은 `next dev`(Turbopack). 임시로만 `next dev --webpack` |
| FE에서 stations/health 실패 | BE가 8000에서 떠 있는지, `NEXT_PUBLIC_API_BASE_URL` 확인 |
| stations 빈 목록 | DB 미설정·service TODO 상태면 정상(빈 배열). DB 연동은 구현 후 |
| OAuth 버튼 무반응 | `startOAuthRedirect` 등 아직 TODO — UI 스켈레톤만 동작 |

### 7. Git / 시크릿 규칙 (팀 공통)

- 커밋 금지: `.env`, `.env.local`, 실키, DB 비번, JWT/OAuth 시크릿
- 커밋 OK: `.env.example`, README, `docs/*` (이 파일 포함), 소스
- README는 외부 공개용 → 어필·스택·Quick start, 실값 금지 (`docs/rules/05_readme.md`)
- Agent가 `api/`를 수정할 때는 **기본으로 담당자 허락** (`docs/rules/01_agent_permissions.md`)

### 8. 합의 한 줄 (구현 시 잊지 말 것)

- API 응답 **camelCase**, `availableCount` **null ≠ 0**
- 지도 **TMAP**, 마커 좌표는 **BE(DB)**, 목록 거리 **Haversine(BE)**
- 반경 기본 **3km** / limit **50** (UI 3·5·10)
- OAuth는 **리다이렉트만** (팝업 없음). 지도 상태 복원은 `returnUrl` 쿼리

---

## 요약 (2026-07-24 기준)

| 구분 | 내용 |
|---|---|
| 진행 단계 | 스켈레톤 구축 · DB/외부 연동 전 |
| FE | `/map`·로그인/가입 UI, `locationStore` follow/현위치, places 검색→BE 연동 |
| BE | FastAPI 뼈대, stations/auth, **places TMAP POI 프록시** (`GET /api/v1/places/search`) |
| 문서 | README 공개용, stations/auth 계약, rules, TMAP env=`NEXT_PUBLIC_TMAP_MAP_KEY`/`TMAP_APP_KEY` 확정 |
| Git | `web/`·`api/` 별도 리포. 상위는 git 없음 |
| 다음 | stations DB → 검색 UX 확인 → OAuth/세션 → 위치 watch → 포인트 |

기준 합의: 워크스페이스 `docs/프로젝트_현황_및_합의사항_20260723.md` (변수명·코드 의미 변경 금지)

---

## 2026-07-24 — 프로젝트 스켈레톤 생성

### 한 일
- 상위 `ev-daegue_eta`는 git 없음(로컬 워크스페이스). `web/`·`api/` 각각 별도 git 리포.
- **BE (`api/`)**: FastAPI + SQLAlchemy 뼈대. `/health`, stations 라우트(시그니처·TODO), auth/points·기타 도메인 스켈레톤. camelCase 응답(`CamelModel`). `DB_*` → `mysql+pymysql` 조립. FE/BE TMAP 키 이름 분리.
- **FE (`web/`)**: Next.js(App Router) + TypeScript + Tailwind + zustand. 흰 배경 Discord풍 셸. 반경 UI 3/5/10km. TMAP 플레이스홀더. stations API 클라이언트.
- env example: `api/.env.example`, `web/.env.example` (실값 없음).
- API 계약: `api/docs/stations_api.md`, FE 요약 `web/docs/fe_rules.md`.
- 로컬 Next: Application Control → 제외 폴더 후 Turbopack 복귀.
- Fold5 커버폭 TopBar 로그인 버튼 축소.

### 합의 기준
- stations: 실DB 방향, `availableCount` null≠0, 반경 기본 3km·limit 50.
- 지도: TMAP. 마커=DB→BE. 거리=Haversine(BE).

### 미완 / 다음
- stations DB 조회, TMAP SDK, OAuth/포인트 실로직.

---

## 2026-07-24 — 규칙·공개 README

### 한 일
- `docs/rules/` + `.cursor/rules/` (BE 사전 허락, 시크릿 금지, teamdeveloper 로그, README 공개 규칙).
- `web/README.md` · `api/README.md` Git 공개용 재작성.

### 다음
- 구현 후 본 파일 append + 리포 docs 동기화.

---

## 2026-07-24 — 로그인/인증 UX 스켈레톤 (1주차)

### 한 일
- FE: `/map`, `/login`, `/signup`, `LoginBottomSheet`, returnUrl 유틸, authStore, OAuth redirect 자리.
- 로그인: 카카오·Google·네이버·일반 회원가입 버튼 (버튼 단위 주석 가능).
- BE: `me` / `logout` / `{provider}/login` / `callback` 시그니처, `validate_return_url`.
- 문서: `auth_api.md`, `auth_ux.md`. 비즈니스 로직은 TODO.

### 결정
- OAuth 리다이렉트 통일(팝업 없음). 지도 핵심 상태=URL, 부가 UI=sessionStorage.

### 다음
- OAuth·세션·me·회원가입 API 사람이 구현.

---

## 2026-07-24 — teamdeveloper 온보딩 섹션 추가

### 한 일
- 본 문서 상단에 팀원용 **세팅 순서·실행 명령·포트·env 키 이름·트러블슈팅·Git 규칙** 추가 (실값 없음).

---

## 2026-07-24 — locationStore 뼈대 (공유 현위치)

### 한 일
- FE: `types/location.ts`, `stores/locationStore.ts` 추가 (`coords` / `source` / `follow` / `testMode` / `locateOnce`·`startWatch` stub).
- `mapStore`에서 `userLocation` 제거 — 지도 카메라(`center`)와 사용자 위치 분리.
- `AppShell`·`MapView`가 `locationStore` 소비 (반경 API origin·마커·현위치 버튼 follow).

### 결정
- 현위치는 여러 컨슈머(지도·반경검색·거리·추후 네비)가 쓰므로 전용 zustand store.
- 테스트 모드는 별도 페이지가 아니라 같은 store + `testMode`/`setTestCoords`.

### 다음
- `startWatch` 실구현, 지도 클릭 테스트 입력, TMAP 마커로 coords 투영, `FEATURES.moveToMyLocation` 연동.

---

## 2026-07-24 — 현위치 버튼 1회만 이동 버그 정리

### 한 일
- `locationStore`: `locateOnce`를 실제 Promise로 수정, `requestFollow` + `followEpoch` 추가 (같은 좌표라도 재이동).
- `MapView`: 카메라 경로 단일화 — follow→`mapStore.center`→TMAP `setCenter`. 버튼에서 직접 `map.setCenter` 제거.
- `MapSearchBar` 장소 선택 시 `follow` 해제.

### 결정
- 현위치 탭마다 `followEpoch`를 올려 이펙트가 다시 돌게 함. GPS는 버튼마다 `locateOnce`로 갱신.

### 다음
- `FEATURES.moveToMyLocation` true 후 실기기/브라우저에서 반복 탭 확인. TMAP 마커로 coords 투영.

---

## 2026-07-24 — 현위치 거부 먹통·1회 이동 재수정

### 한 일
- AppShell `locateOnce` rejection catch (위치 OFF 시 unhandled rejection 오버레이 방지).
- 현위치: 캐시 좌표로 즉시 `map.setCenter` 후 GPS 갱신 (이펙트 의존 제거).
- 권한 거부 메시지·버튼 옆 에러 표시. `FEATURES.moveToMyLocation` true.

### 결정
- 카메라 이동은 버튼에서 imperative. drag/현위치 후에는 center sync 스킵.

### 다음
- 위치 OFF·허용·지도 팬 후 ◎ 반복 탭 확인.

---

## 2026-07-24 — 현위치 TMAP Marker 연결

### 한 일
- `MapView`: 화면 중앙 파란점 overlay 제거. `locationStore.coords` → `Tmapv2.Marker` create/setPosition.

### 다음
- 커스텀 아이콘·accuracy 원·`startWatch` 연동(선택).

---

## 2026-07-24 — TMAP env 이름 확정

### 한 일
- FE 지도 SDK 키: `NEXT_PUBLIC_TMAP_APP_KEY`(가칭) → **`NEXT_PUBLIC_TMAP_MAP_KEY`** 로 개명.
- `web/.env.example`·README, `api/.env.example`·README, `docs/rules/02`, 합의 문서 §3.1/§10/TBD 반영.
- BE `TMAP_APP_KEY` 용도 주석에 POI/장소검색 포함 (ETA·길찾기와 동일 서버 키).

### 결정
- 지도 SDK = FE 공개 키. POI/검색·ETA REST = BE만. 장소검색은 Next BFF 아님 → FastAPI 프록시.
- BE 담당 확인 후 문서·example 선반영 (엔드포인트 구현은 후속).

### 다음
- `MapView`에서 `NEXT_PUBLIC_TMAP_MAP_KEY` 실제 로드.
- BE 장소검색 프록시 시그니처·`searchTmapPlaces()` → 우리 API 호출.

---

## 2026-07-24 — places 검색 최소 연동

### 한 일
- BE `places`: import 경로 수정(`services_tmap`), `PlaceResult` 응답, `get_settings().tmap_app_key`로 TMAP POI 호출.
- 빈 `tmap.py` 제거. FE `searchTmapPlaces` → `GET /api/v1/places/search`.

### 결정
- 기존 `router` / `client` / `services_tmap` / `place` 파일명 유지(최소 수정).

### 다음
- 지도에서 검색 결과 선택 → 이동 UX 확인. 키 없으면 503.

---

## 기록 규칙

1. 날짜 헤더(`## YYYY-MM-DD — 제목`)로 추가.
2. 한 일 / 결정 / 다음만 짧게. 키·토큰·DB 비번·실 `.env` 값 금지.
3. Agent가 의미 있는 구현을 마치면 이 파일에 한 블록 append.
4. Git 올릴 때 `web/docs/teamdeveloper.md`, `api/docs/teamdeveloper.md` 동기화.
5. 새 블록 추가 시 위 **요약** 표도 최신화. 온보딩 섹션이 바뀌면 상단도 함께 수정.
