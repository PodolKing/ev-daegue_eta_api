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
#모바일 실행용
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# macOS / Linuxv
# source .venv/bin/activate
# pip install -r requirements.txt
# cp .env.example .env

.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

> **이 명령만으로 “앱(지도 UI)”이 뜨는 것은 아님.**  
> - BE API만 기동 (`http://localhost:8000`) — `/health`, `/docs` 확인용.  
> - 기본 바인딩은 **이 PC(localhost)만** 접속 가능. 같은 Wi‑Fi 폰에서는 안 열림.  
> - 지도·검색 화면은 아래 **Frontend**도 같이 켜야 함 (`http://localhost:3000/map`).  
> - 폰 테스트는 §7 — `--host 0.0.0.0` + `npm run dev:lan` + LAN IP env.

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

### 4. 일상 실행 — PC 로컬 앱 테스트 (두 터미널)

**지도 UI까지** 보려면 BE + FE **둘 다** 필요.

#### 사전 체크 (PC)

| 항목 | 기대 |
|---|---|
| `web/.env.local` → `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` (폰용 LAN IP면 PC에선 API가 꼬일 수 있음 → PC만 볼 때 localhost로) |
| `api/.env` → `CORS_ORIGINS` | `http://localhost:3000` 포함 |
| `web/.env.local` → `NEXT_PUBLIC_TMAP_MAP_KEY` | 값 있음 (지도) |
| `api/.env` → `TMAP_APP_KEY` | 값 있음 (검색 등) |

> **지금 로컬 상태(검토 시점):** 모바일용으로 `NEXT_PUBLIC_API_BASE_URL=http://172.30.1.7:8000`, `CORS_ORIGINS`에 `http://172.30.1.7:3000`이 들어가 있음.  
> PC 브라우저만 쓸 때는 API URL을 `http://localhost:8000`으로 되돌리거나, PC에서도 `http://172.30.1.7:3000`으로 접속하면 됨.

#### 풀 실행 명령 (PC · 워크스페이스 `ev-daegue_eta` 기준)

```powershell
# ===== 터미널 A — Backend (API) =====
cd c:\Users\user\Desktop\ev-daegue_eta\api
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# ===== 터미널 B — Frontend (지도 UI) =====
cd c:\Users\user\Desktop\ev-daegue_eta\web
npm run dev
```

| 구분 | URL |
|---|---|
| 앱(지도) | http://localhost:3000/map |
| API 문서 | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

| 명령 | 되는 것 | 안 되는 것 |
|---|---|---|
| uvicorn … `--port 8000` (host 생략) | 같은 PC에서 API | 폰·다른 기기에서 API |
| 위 + `npm run dev` | **PC에서 앱 전체** | 같은 Wi‑Fi 폰 (localhost = 폰 자신) |
| §7 (`--host 0.0.0.0` + `dev:lan`) | **폰에서 앱** | — |

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
| uvicorn만 켰는데 지도가 안 보임 | 정상 — FE(`npm run dev`)도 켜고 `http://localhost:3000/map` |
| 폰에서 localhost로 접속 실패 | 정상 — §7 LAN IP + `--host 0.0.0.0` 사용 |
| stations 빈 목록 | DB 미설정·service TODO 상태면 정상(빈 배열). DB 연동은 구현 후 |
| OAuth 버튼 무반응 | `startOAuthRedirect` 등 아직 TODO — UI 스켈레톤만 동작 |

### 7. 같은 Wi‑Fi 모바일 테스트 (LAN)

폰의 `localhost`는 폰 자신이다. PC LAN IP로 FE/BE를 열어야 한다.  
PC 전용 명령(`uvicorn … --port 8000` only, host 생략)으로는 **폰 앱 테스트가 안 된다.**  
`--host 0.0.0.0`만으로는 부족하고, **FE `dev:lan` + env(CORS·API base)** 가 같이 필요하다.

**현재 예시 IP:** `172.30.1.7` (공유기 재연결·DHCP면 바뀔 수 있음. `ipconfig`의 IPv4로 확인)

#### 세팅 검토 체크리스트 (값·키 내용은 커밋/문서에 적지 말 것)

| # | 항목 | 검토 결과(예시 IP `172.30.1.7` 기준) |
|---|---|---|
| 1 | `api/.env` → `CORS_ORIGINS` | `http://localhost:3000,http://172.30.1.7:3000` 형태여야 함 |
| 2 | `web/.env.local` → `NEXT_PUBLIC_API_BASE_URL` | `http://172.30.1.7:8000` (trailing slash 없음) |
| 3 | `web/package.json` → `dev:lan` | `next dev --hostname 0.0.0.0` 있음 |
| 4 | BE 실행 | **`--host 0.0.0.0 --port 8000`** 필수 |
| 5 | FE 실행 | **`npm run dev:lan`** 필수 |
| 6 | (선택) TMAP 콘솔 | 지도 키 도메인 제한 시 `http://172.30.1.7:3000` 허용 |
| 7 | Windows 방화벽 | 3000·8000 인바운드 허용 |

> **검토 시점:** 위 1~3은 로컬 env/스크립트에 반영됨. 4~5는 아래 명령으로 실행. 실 키·비밀번호는 이 문서에 적지 않음.

#### 풀 실행 명령 (모바일 · 워크스페이스 `ev-daegue_eta` 기준)

```powershell
# ===== 터미널 A — Backend (LAN에 API 공개) =====
cd c:\Users\user\Desktop\ev-daegue_eta\api
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ===== 터미널 B — Frontend (LAN에 Next 공개) =====
cd c:\Users\user\Desktop\ev-daegue_eta\web
npm run dev:lan
```

| 어디서 | URL |
|---|---|
| 폰 브라우저 (같은 Wi‑Fi) | http://172.30.1.7:3000/map |
| 폰에서 API 직접 확인(선택) | http://172.30.1.7:8000/health |
| PC에서도 LAN으로 열기 | http://172.30.1.7:3000/map |

`NEXT_PUBLIC_*`를 바꿨으면 **터미널 B(Next)를 반드시 재시작**.

#### IP가 바뀌었을 때 수정할 곳

코드(`config.py` 기본값)는 바꿀 필요 없음. **로컬 env·실행·(선택) TMAP 콘솔만.**

| 위치 | 수정 내용 |
|---|---|
| `api/.env` | `CORS_ORIGINS`에 `http://<새IP>:3000` 포함 (예: `http://localhost:3000,http://172.30.1.7:3000`) |
| `web/.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://<새IP>:8000` (trailing slash 없음). 바꾼 뒤 **Next 재시작** |
| (선택) TMAP 콘솔 | 지도 키에 도메인/Referer 제한이 있으면 `http://<새IP>:3000` 허용. 제한 없으면 생략 |
| 실행 명령 | 아래 풀 명령의 IP만 새 값으로 + API는 계속 `--host 0.0.0.0` |
| Windows 방화벽 | 3000·8000 인바운드가 막히면 같은 망인데도 안 열림 |

**커밋하지 말 것:** `api/.env`, `web/.env.local` (실 IP·키).  
참고용 키 이름만: `api/.env.example`, `web/.env.example` 주석.

PC 전용으로 되돌릴 때:

| 파일 | 값 |
|---|---|
| `api/.env` | `CORS_ORIGINS=http://localhost:3000` (모바일 Origin 빼도 됨) |
| `web/.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |
| 실행 | §4 풀 실행 명령 (host 없는 uvicorn + `npm run dev`) |

### 8. Git / 시크릿 규칙 (팀 공통)

- 커밋 금지: `.env`, `.env.local`, 실키, DB 비번, JWT/OAuth 시크릿
- 커밋 OK: `.env.example`, README, `docs/*` (이 파일 포함), 소스
- README는 외부 공개용 → 어필·스택·Quick start, 실값 금지 (`docs/rules/05_readme.md`)
- Agent가 `api/`를 수정할 때는 **기본으로 담당자 허락** (`docs/rules/01_agent_permissions.md`)

### 9. 합의 한 줄 (구현 시 잊지 말 것)

- API 응답 **camelCase**, `availableCount` **null ≠ 0**
- 지도 **TMAP**, 마커 좌표는 **BE(DB)**, 목록 거리 **Haversine(BE)**
- 반경 UI **1·2·3 km** / limit **50·100·200** (FE `limitForRadiusKm`, BE `MAX_LIMIT` — 상세는 2026-07-27 limit 조정 위치 블록)
- OAuth는 **리다이렉트만** (팝업 없음). 지도 상태 복원은 `returnUrl` 쿼리

---

## 요약 (2026-07-27 기준)

| 구분 | 내용 |
|---|---|
| 진행 단계 | 지도 **동결** · 모바일 검색 토글 · 위치 안내 |
| FE | `/map` 정상. SDK=`loadSdk` **topopentile 우선**. 검색 아이콘 토글. 반경 fitBounds=사용자 탭만 |
| BE | FastAPI 뼈대, stations/auth, places TMAP POI 프록시 |
| 문서 | **`docs/important.md` 필독(잠금)**. rules, MAP_KEY/APP_KEY 분리 |
| Git | `web/`·`api/` 별도 리포. 상위는 git 없음 |
| 다음 | stations 좌표 마커 → OAuth/세션 → 위치 watch → 포인트 (**지도 SDK는 잠금**) |

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

## 2026-07-27 — 같은 Wi‑Fi 모바일(LAN) 테스트 세팅

### 한 일
- 로컬: `api/.env` `CORS_ORIGINS`에 LAN FE Origin 추가, `web/.env.local` API base를 PC LAN IP(`172.30.1.7`)로 설정 (커밋 대상 아님).
- FE `npm run dev:lan` (`next dev --hostname 0.0.0.0`) 추가. 온보딩에 uvicorn `--host 0.0.0.0` + IP 변경 시 수정 파일 표 추가.
- `web/README.md`·`web/docs/fe_rules.md` 반경 문구를 UI 실제값 **1 / 3 / 5 km**에 맞춤.
- `.env.example`에 모바일/LAN 주석만 보강 (실 IP·키 없음).

### 결정
- LAN IP는 DHCP로 바뀔 수 있음 → `api/.env`·`web/.env.local`(·선택 TMAP 콘솔)만 갱신. `config.py` 기본값 불변.
- 시크릿·실키는 teamdeveloper에 적지 않음.

### 다음
- 폰에서 `http://<PC-LAN-IP>:3000/map` 접속 확인. 지도 키 도메인 제한 있으면 콘솔에 Origin 추가.
- PC만 쓸 때는 API/FE env를 localhost로 되돌리기.

---

## 2026-07-27 — 좁은 화면 충전소 목록 토글 (map-first)

### 한 일
- `useCompactLayout`: `analyticsDeviceType() === "mobile"` **또는** width ≤ 400px.
- `AppShell`: compact면 목록 기본 닫힘. `<md` 바텀시트·`md+` 사이드 패널 모두 토글. 우측 하단「목록」버튼.
- `MapView`: 시트 열림 시 현위치/반경 FAB 위치 상향.

### 결정
- 좁은 화면은 지도 우선. 목록은 필요할 때만.

### 다음
- 실기기·≤400px에서 지도 가시 영역·토글 확인. IconRail(68px) 축소는 후속 선택.

---

## 2026-07-27 — 좁은 화면 IconRail(메뉴) 토글 정정

### 한 일
- 오해 수정: 토글 대상은 **충전소 목록이 아니라** 좌측 IconRail(지도·즐겨찾기·포인트·설정).
- 충전소 목록(바텀시트/`md+` 패널)은 **기본 열림** 유지.
- compact(mobile 또는 ≤400px)에서 레일 기본 닫힘 +「메뉴」버튼으로 on/off.

### 결정
- 좁은 화면에서 가로 68px 레일을 접어 지도 폭 확보.

### 다음
- 실기기에서 메뉴 토글·목록 상시 표시 확인.

---

## 2026-07-27 — 로컬 실행: uvicorn만 vs 앱 전체 vs 폰

### 한 일
- 온보딩 §2·§4·§6·§7 보강: `uvicorn … --port 8000` = **PC에서 API만**. 지도 UI는 FE 동시 기동. 폰은 `--host 0.0.0.0` + `dev:lan`.

### 결정
- host 생략 uvicorn ≠ 앱 테스트 완료. PC 앱 = §4, 모바일 = §7.

### 다음
- (없음 — 문서 정정)

---

## 2026-07-27 — LAN 세팅 검토 + 풀 실행 명령 정리

### 한 일
- 로컬 검토: `CORS_ORIGINS`에 LAN Origin, FE API base=`http://172.30.1.7:8000`, `dev:lan` 스크립트, PC IPv4=`172.30.1.7` 확인 (실 키는 문서 미기재).
- §4·§7에 `cd` 포함 **풀 실행 명령**·체크리스트 반영.

### 결정
- 폰 테스트 = env(1~3) + `--host 0.0.0.0` + `npm run dev:lan` 세트.

### 다음
- 두 터미널로 §7 명령 실행 후 폰에서 `http://172.30.1.7:3000/map` 확인.

---

## 2026-07-27 — 메뉴(IconRail) compact 기준 400→500px

### 한 일
- `COMPACT_MAX_WIDTH_PX` 400 → **500**. mobile UA 또는 width ≤ 500이면 레일 기본 숨김.

### 결정
- 일반 폰·좁은 창에 여유 있게 맞춤.

### 다음
- (없음)

---

## 2026-07-27 — IconRail compact: 터치 기기 기준 (CSS 폭 프리셋 폐기)

### 한 일
- `useCompactLayout`: DevTools CSS 폭(344/412/500)·`analyticsDeviceType` 제거.
- 실기기: `(hover: none) and (pointer: coarse)` → 항상 compact. 그외 `max-width: 767px`.
- `railOpen` 기본 `false` (폰에서 레일 깜빡임 방지).

### 결정
- 레이아웃은 UA/에뮬 CSS 숫자가 아니라 **포인터·호버(실기기)** + Tailwind `md` 경계.

### 다음
- Ultra/Fold 실기기에서 메뉴 기본 닫힘·「메뉴」토글 확인.

---

## 2026-07-27 — 모바일 지도 미표시·버튼 먹통 수정

### 한 일
- `MapView`: TMAP SDK를 `apis.openapi.sk.com/tmap/jsv2?appKey=` + `NEXT_PUBLIC_TMAP_MAP_KEY`로 로드 (키 없는 topopentile 스크립트 제거).
- 좌표 없는 임시 station 버튼 overlay·중앙 파란점 제거 (지도·FAB 터치 차단 원인).
- 모바일 하단 시트·현위치/반경/메뉴를 `42dvh` 기준으로 맞추고 FAB/메뉴 z-index 상향. 시트 바깥은 `pointer-events-none`.

### 결정
- 충전소 지도 표시는 이후 좌표 기반 TMAP Marker로만. 임시 HTML 버튼 오버레이 금지.

### 다음
- 폰에서 하드 새로고침 후 타일·◎·반경·메뉴 토글 확인. TMAP 콘솔에 LAN Origin 허용.

---

## 2026-07-27 — TMAP z-index 가림 + 메뉴 위치

### 한 일
- `MapView`: 지도 컨테이너를 `z-0` 트랩으로 감싸 SDK 내부 z-index가 FAB/검색을 덮지 않게 함. UI는 `pointer-events` 분리 레이어.
- 모바일「메뉴」버튼을 하단→**상단 우측**(검색 옆)으로 이동해 시트/상세와 겹침 제거.

### 다음
- FE 재시작(`NEXT_PUBLIC_*`) + 폰 하드 새로고침 후 재확인. 폰은 `npm run dev:lan` 권장.

---

## 2026-07-27 — TMAP LatLng 미준비 + allowedDevOrigins

### 한 일
- `MapView`: `LatLng`/`Map`이 constructor일 때만 create (부분 로드 크래시 방지), 폴링 재시도.
- `next.config.ts`: `allowedDevOrigins`에 LAN IP (`172.30.1.7` 등) — 폰에서 Next 폰트/HMR 차단 해제.

### 다음
- **FE 서버 재시작** 필수(`next.config` 반영). 폰 강력 새로고침.

---

## 2026-07-27 — 모바일 검색 토글 + 위치 안내 문구

### 한 일
- `MapSearchBar`: compact에서 검색 **아이콘 ↔ 기존 필 검색바** 토글 (바텀시트 아님). 데스크톱은 항상 검색바.
- `MapView`: 위치 실패 안내를 FAB 위 **닫기 가능한 배너**로 표시.
- `locationStore`: insecure context(LAN HTTP)면 geolocation 전에 안내. 권한 거부 문구 명확화.

### 결정
- 검색 토글 기준은 메뉴와 동일 (`useCompactLayout`).
- HTTPS/localhost 위치 제한은 **브라우저 Geolocation(secure context) 정책** — TMAP 무관.

### 다음
- (지도 로드 이슈는 아래 블록)

---

## 2026-07-27 — 지도 안 뜸 (SDK Strict Mode 로드 레이스)

### 한 일
- `lib/tmap/loadSdk.ts` 추가: jsv2를 **페이지당 1회** 로드하는 싱글톤 (실패 시 재시도, Strict remount 안전).
- `MapView`: 폴링/`onload=null` 제거 → `ensureTmapSdk()` 후 `Map("ev-tmap-map")` 생성. 오류 메시지에 `Tmapv2`/`Map`/`LatLng` 진단 포함.

### 결정
- “SDK 준비 안 됨”은 스크립트 실패·키/도메인 거부·로드 레이스가 타임아웃으로 뭉개진 경우가 많음. 진단 문구로 구분.

### 다음
- 강력 새로고침 후 상단 빨간 문구 **전체** 확인 (괄호 안 진단 포함).
- 브라우저 DevTools → Network에서 `jsv2` 상태(200/403) 확인. TMAP 콘솔에 `localhost` 도메인 허용.

---

## 2026-07-27 — TMAP SDK 잠금 + Map/LatLng fallback

### 한 일
- `loadSdk.ts`: 공식 jsv2 후 `Map`/`LatLng` 없으면 **topopentile fallback**.
- Cursor rule `tmap-sdk-lock.mdc` + `docs/rules/01_agent_permissions.md`: SDK 로드/MapView 부트스트랩은 **허락 없이 수정 금지**.

### 결정
- 시행착오 반복 방지. UI 작업 시 SDK 로더를 같이 건드리지 않음.
- jsv2 우선, stub만 오면 topopentile.

### 다음
- `/map` 강력 새로고침으로 지도 표시 확인. 뜬 뒤 SDK 잠금 준수.

---

## 2026-07-27 — important.md (TMAP 잠금 정리)

### 한 일
- `docs/important.md` 작성: TMAP SDK 잠금 경로, 로드 순서(jsv2→topopentile), 키 분리, 시행착오 표, 변경 시 허락 절차.
- `web/docs/`, `api/docs/` 동기화. rules README·tmap-sdk-lock·01_agent_permissions에서 링크.

### 결정
- 지도 정상 후 SDK/부트스트랩은 **수정 전 사용자에게 묻기**. Agent 규칙 + important 문서로 고정.

### 다음
- (없음)

---

## 2026-07-27 — TMAP jsv2 stub 빠른 fallback (사용자 허락)

### 한 일
- `loadSdk.ts`: jsv2 stub(`Tmapv2`만 있고 Map/LatLng 없음) ~350ms면 즉시 topopentile. jsv2 최대 대기 8s→~1.2s.
- `docs/important.md` 로드 타이밍 문구 갱신.

### 결정
- 첫 지도 지연의 주원인은 stub 8초 대기. 공식 경로 유지하되 fail-fast.

### 다음
- 웹/폰에서 첫 로드 체감 확인.

---

## 2026-07-27 — 첫 로드 순서·웹 줌아웃 수정 (사용자 허락)

### 한 일
- `loadSdk`: **topopentile 우선** (jsv2 stub 왕복 제거).
- `RadiusControl`: 첫 지도 붙을 때 `fitBounds` 금지 — 사용자가 반경 버튼 누를 때만.
- `returnUrl` 파서: `zoom=0` / `lat=0` 무시. MapView resize 후 줌&lt;11이면 store 줌 복구.

### 결정
- 한반도 풀줌은 레이아웃 전 fitBounds 부작용. 초기 줌은 createMap(15) 유지.

### 다음
- 웹·모바일 강력 새로고침 후 대구 근처 줌·첫 타일 속도 확인.

---

## 2026-07-27 — 지도 동결 문서화 (수정 잠금)

### 한 일
- `docs/important.md` 전면 정리: 동결 상태표, 잠긴 경로(+`RadiusControl`), 로드·줌·fitBounds 스펙, 시행착오 표, 잠금 해제 절차.
- `.cursor/rules/tmap-sdk-lock.mdc` FROZEN + RadiusControl 포함. `01_agent_permissions` / `project-overview` / rules README 갱신.
- `web/docs`·`api/docs` 동기화.

### 결정
- **이제부터** 지도 SDK·부트스트랩·반경 fit은 **허락 없이 수정 금지.**

### 다음
- (없음 — 잠금 유지)

---

## 2026-07-27 — 반경 고정 줌 프리셋 (사용자 허락)

### 한 일
- `RadiusControl`: 반경 탭 시 `fitBounds` 제거 → 고정 줌 **1→16 / 3→15 / 5→14** + 중심 유지. 원 tint↑·stroke 얇게(잘림 허용).
- `docs/important.md`·`tmap-sdk-lock.mdc` 스펙 갱신. `web/docs`·`api/docs` 동기화.

### 결정
- 원 전체 맞춤보다 “내 주변” 시야 유지. 프리셋은 체감 후 조정 가능.

### 다음
- 웹·폰에서 1/3/5 전환 시야·원 잘림 체감 확인. 필요 시 줌 숫자만 미세 조정.

---

## 2026-07-27 — stations DB 반경 조회 (ValidationError→CORS 오인)

### 한 일
- `stations/service.py`: bbox→Haversine→`stat_id` 집계→status LEFT JOIN→`availableCount` null≠0.
- `controller`: NotImplemented 빈배열 제거. FE CORS 오류의 실원인은 500(필드명/`StationItem` 검증 실패).

### 결정
- `/stations`는 DB만 조회. 외부 status API는 요청 경로에 넣지 않음.

### 다음
- FE 마커. status 테이블 적재 확인(`availableCount` null이면 수집 파이프).

---

## 2026-07-27 — stations router/controller 역할 복구

### 한 일
- `router.py`에 controller 로직이 섞여 `ImportError: cannot import name 'router'` 발생 → FastAPI `APIRouter` 복구.
- `controller.get_stations`를 near(`list_stations_near`)만 호출하도록 정리. 빈 `route_service.py` 제거.

### 결정
- 계약 유지: `GET /api/v1/stations?lat&lng&radiusKm&limit` (viewport mode 미도입).

### 다음
- uvicorn 기동·`/api/v1/stations` near 응답 확인.

---

## 2026-07-27 — stations 반경별 limit + FE 재조회 고정

### 한 일
- BE `MAX_LIMIT` 100→**150**, router `le=150`.
- FE `limitForRadiusKm`: **1→50 / 3→100 / 5→150**. `AppShell`이 `radiusKm` 변경 시 재요청(요청 seq로 stale 응답 무시).
- `stations_api.md` limit 상한·UI 반경 표기 갱신.

### 결정
- limit는 FE가 반경별로 넘김. BE는 상한만 150까지 허용.

### 다음
- 1/3/5 탭 시 Network에 `radius_km`·`limit` 변경 요청이 나가는지 확인.

---

## 2026-07-27 — stations limit 조정 위치 정리 + 5km 200건

### 한 일
- 5km limit **150→200**: FE `web/src/lib/api.ts` `limitForRadiusKm`, BE `service.MAX_LIMIT`, router `Query(le=MAX_LIMIT)`.
- 아래 **limit/반경 상한이 어디서 정해지는지** 문서화.

### 결정 — stations limit·반경 상한 (수정 시 같이 맞출 곳)

| 역할 | 파일 | 내용 |
|------|------|------|
| **반경별 개수 (본체)** | `web/src/lib/api.ts` → `limitForRadiusKm` | UI 1/2/3 km → **50 / 100 / 200** |
| **BE limit 상한** | `api/.../stations/service.py` → `MAX_LIMIT`, `clamp_limit()` | 요청 limit 최대값 |
| **API 검증** | `api/.../stations/router.py` → `Query(..., le=MAX_LIMIT)` | FastAPI 422 방지 |
| **기본값** | `service.DEFAULT_LIMIT`(50), `DEFAULT_RADIUS_KM`(3) | 쿼리 생략 시 |
| **반경 상한** | `service.MAX_RADIUS_KM`(10), router `radius_km le=10` | UI는 1·2·3, API 직접 호출은 10까지 |
| **전달만** | `controller.py` | 받은 `limit`을 `list_stations_near`에 전달 |

3km 건수만 바꿀 때: **FE `limitForRadiusKm` + BE `MAX_LIMIT` ≥ 그 값 + router `le`**.

### 다음
- 3km 탭 시 `limit=200` 요청·응답 count 확인.

---

## 2026-07-27 — 반경 UI 1/2/3 km + 줌·limit 재정렬

### 한 일
- UI 반경 **1·3·5 → 1·2·3 km**. 고정 줌 **1→16 / 2→15 / 3→14** (`RadiusControl`, 사용자 승인 후 동결 스펙 갱신).
- limit **1→50 / 2→100 / 3→200** (`limitForRadiusKm`). `RadiusKm`·`returnUrl`·README·`important.md`·`stations_api` 동기화.

### 결정
- 반경 탭은 가까운 체감 유지. 원 잘림 허용·`fitBounds` 금지 원칙은 유지.

### 다음
- 1/2/3 탭 시 Network `radius_km`·`limit`·시야 체감 확인.

---

## 기록 규칙

1. 날짜 헤더(`## YYYY-MM-DD — 제목`)로 추가.
2. 한 일 / 결정 / 다음만 짧게. 키·토큰·DB 비번·실 `.env` 값 금지.
3. Agent가 의미 있는 구현을 마치면 이 파일에 한 블록 append.
4. Git 올릴 때 `web/docs/teamdeveloper.md`, `api/docs/teamdeveloper.md` 동기화.
5. 새 블록 추가 시 위 **요약** 표도 최신화. 온보딩 섹션이 바뀌면 상단도 함께 수정.
