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
`--host 0.0.0.0` + FE `npm run dev:lan` 필요.

**공유기 on/off·DHCP:** PC IPv4(`172.30.1.x`)만 바뀐다. **DB 계정·비밀번호·스키마는 안 바뀐다.**

| 구분 | 공유기 재시작 영향 | 팀 권장 |
|---|---|---|
| DB (`DB_HOST`) | 없음 (각자 `127.0.0.1`) | **팀원끼리 LAN IP로 DB 공유하지 말 것** |
| 폰→PC API/FE | PC IP만 바뀜 | 폰에서 `http://<새IP>:3000`만 다시 입력 |
| CORS / API base | 코드가 `172.30.1.*` 허용 + FE는 page hostname:8000 | IP 바뀔 때 env 재수정 불필요 |

#### 세팅 검토 체크리스트 (값·키 내용은 커밋/문서에 적지 말 것)

| # | 항목 | 검토 |
|---|---|---|
| 1 | `api/.env` → `CORS_ORIGINS` | `http://localhost:3000`면 충분 (LAN은 `CORS_ORIGIN_REGEX` 기본값) |
| 2 | `web/.env.local` → `NEXT_PUBLIC_API_BASE_URL` | PC용 `http://localhost:8000` 유지. 폰은 hostname 자동 |
| 3 | `web/package.json` → `dev:lan` | `next dev --hostname 0.0.0.0` |
| 4 | BE 실행 | **`--host 0.0.0.0 --port 8000`** |
| 5 | FE 실행 | **`npm run dev:lan`** |
| 6 | (선택) TMAP 콘솔 | 도메인 제한 시 LAN Origin 허용 여부 확인 |
| 7 | Windows 방화벽 | 3000·8000 인바운드 |

#### 팀원과 같이 작업할 때 (DB)

1. **기본:** 각자 PC에 MariaDB + `DB_HOST=127.0.0.1`. `.env`는 커밋하지 않음.
2. **스키마/시드:** git·덤프·마이그레이션으로 맞추고, **접속 주소는 LAN IP로 공유하지 않음** (DHCP면 매번 깨짐).
3. **공통 DB가 필요하면:** 고정 호스트(클라우드/서버 DNS) 한 곳을 쓰고, 접속 정보는 메신저 등으로만 공유 (git 금지).
4. **코드·API 계약**만 리포로 공유. LAN IP·DB 비번은 문서/커밋에 넣지 않음.

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
| 폰 브라우저 (같은 Wi‑Fi) | `http://<PC-IPv4>:3000/map` (`ipconfig`로 확인) |
| 폰에서 API 직접 확인(선택) | `http://<PC-IPv4>:8000/health` |
| PC 브라우저 | http://localhost:3000/map |

#### IP가 바뀌었을 때

**보통 env 수정 불필요.** 폰 주소만 새 PC IP로 다시 열면 됨.  
(구버전처럼 `CORS_ORIGINS` / `NEXT_PUBLIC_API_BASE_URL`에 LAN IP를 박아 둔 경우만 정리)

| 위치 | 할 일 |
|---|---|
| 폰 브라우저 | `http://<새IP>:3000/map` |
| `api/.env` / `web/.env.local` | localhost만 쓰면 그대로 |
| (선택) TMAP 콘솔 | Referer 제한이 있으면 새 Origin 허용 |
| Windows 방화벽 | 3000·8000 |

**커밋하지 말 것:** `api/.env`, `web/.env.local`.

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

## 요약 (2026-07-29 기준)

| 구분 | 내용 |
|---|---|
| 진행 단계 | 지도 **동결** · 완속 필터 · 가용 합계/버킷 분해 |
| FE | `/map` 정상. 목록·마커 가용·총대수=`includeSlow`에 맞춤(기본=other). 상세=혼합소 other/slow 분리 |
| BE | stations: `availableCountOther`/`Slow` + `chargerTotalOther`(slow total 없음=total−other) |
| 문서 | **`docs/important.md` 필독(잠금)**. rules, MAP_KEY/APP_KEY 분리 |
| Git | `web/`·`api/` 별도 리포. 상위는 git 없음 |
| 다음 | 혼합소에서 완속 토글 시 마커 `가용/총` 실기 확인 |

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

## 2026-07-28 — LAN 172.30.1.* 고정 없이 폰 테스트 + 팀 DB 안내

### 한 일
- BE: `CORS_ORIGIN_REGEX` 기본값으로 `http://172.30.1.*:<port>` Origin 허용 (DHCP IP 변경 대응).
- FE: `getApiBase()` — 폰에서 page hostname:8000 자동 (LAN IP를 env에 안 박음).
- Next: `allowedDevOrigins`에 `172.30.1.1`–`.254` 포함.
- 온보딩 §7: 공유기 재시작 ≠ DB 변경, 팀원은 `DB_HOST=127.0.0.1` 각자 로컬(또는 고정 DNS 공유 DB).

### 결정
- 팀 협업 시 LAN IP로 DB 공유하지 않음. 코드·스키마만 git, 접속정보는 로컬/메신저.

### 다음
- BE·FE 재시작 후 폰에서 새 IP로 `/map`만 열어 확인. `.env`의 옛 LAN IP는 localhost로 정리해도 됨.

---

## 2026-07-28 — users / favorites ORM 모델 정리

### 한 일
- `stations/models.py`: 깨져 있던 `User`를 DB DDL(`users`)에 맞게 수정.
- `UserRole` enum, `UserFavoriteCharger`(`user_favorite_chargers`) 추가. `ev_charger_info` 복합 FK 반영.

### 결정
- 테이블명 `users` (단수 `user` 아님). 즐겨찾기는 `(user_id, stat_id, chger_id)` 유니크.

### 다음
- auth/favorites API·스키마 연동 시 이 모델 사용.

---

## 2026-07-28 — cars / car_models ORM 추가

### 한 일
- `stations/models.py`에 `CarModel`(`car_models`), `Car`(`cars`) 추가.
- `FuelType`(EV/PHEV), `ChargingPort`(CCS1/NACS/CHADEMO) enum 반영. `cars.user_id` ON DELETE CASCADE.

### 결정
- `car_model_id`·`nickname`·`custom_model_name` nullable (커스텀 차명 허용).

### 다음
- 차량 CRUD API 연동 시 이 모델 사용.

---

## 2026-07-28 — status sync 1차 연동 (경고·일일한도)

### 한 일
- `stations/sync.py`: 공공 `getChargerStatus` 호출 → `ev_charger_status` bulk upsert. 기동 경고(PC·운영 동시 수집 금지), 프로세스 일일 outbound soft cap, `max_instances=1`.
- `main.py` lifespan에서 스케줄러 start/stop. `EV_STATUS_SYNC_ENABLED` 기본 false.
- `config` / `.env.example`에 sync 관련 env 이름 추가. `APScheduler` requirements 반영.

### 결정
- 수집은 **한 호스트만** ON. PC 개발은 개인 DB + sync OFF. 운영만 true.
- 대구 `zcode=27`, period/interval 5분, 일 한도 기본 400(프로세스 메모리).

### 다음
- 로컬에서 `EV_STATUS_SYNC_ENABLED=true`로 단발 검증 후 바로 OFF. 응답 파싱·키 인코딩 이슈 있으면 보정.
- 운영 반영 시 worker=1, `--reload` 금지.

---

## 2026-07-28 — Agent 프롬프트(수집·info 보강)

### 한 일
- `docs/agent_prompt_ev_charger_sync.md` 추가(복사용 프롬프트·지시 예시·외부 프로그램 골격). `api/docs`·`web/docs` 동기화.

### 결정
- status 5분(BE)과 info 보강(외부/저빈도) 분리. Agent 재시작 시 해당 문서 `@` 첨부.

### 다음
- 외부 info upsert 스크립트는 별도 지시로 구현.

---

## 2026-07-28 — 위치 추적 · 주행 테스트 · stations throttle

### 한 일
1. **타입** (`web/src/types/location.ts`)  
   - `LocationStatus` 설명 보강, `LocationDriveMode`(`off`/`watch`/`test`) 추가.
2. **locationStore** (`web/src/stores/locationStore.ts`)  
   - `startWatch` / `stopWatch`: `watchPosition` + `watchId` / `isWatching`.  
   - `setTestMode(true)` → GPS watch 중지. **`setTestMode(false)`는 watch 자동 시작 안 함**.  
   - `setTestCoords`: testMode일 때만 fake GPS.
3. **RadiusControl**  
   - 원은 `coords`(없으면 map center) 기준 **destroy→재생성**.  
   - TMAP `Circle.setCenter` in-place는 원 소실 회귀로 **사용 안 함**.  
   - 카메라 줌은 **1/2/3 탭만** (동결 유지).
4. **AppShell**  
   - stations 재조회: 반경 변경=즉시, coords는 **200m 또는 4초**(미만은 trailing debounce).
5. **MapView + features**  
   - `FEATURES.locationWatch` / `drivingTestMode`.  
   - FAB: 추적 on/off → `startWatch`/`stopWatch`, follow 연동. 드래그 시 follow off(기존).  
   - FAB: 테스트 on/off. ON이면 지도 **클릭/탭** → `setTestCoords`.  
   - follow 중 coords 변경 시 카메라만 따라감(줌 변경 없음).  
   - SDK 로드·createMap·RadiusControl 카메라 프리셋 **미변경**.

### 결정
- BE 추가 없음(기존 `lat/lng/radius` 조회). 2.5만 건 → 전체 캐시 비추천.  
- **watching ≠ follow**. 차량·배터리 → 추적 off 필요.  
- 테스트 off ≠ GPS on (명시적 `startWatch`만).  
- 테스트 입력은 모바일 친화 **지도 탭** 우선.  
- 개발 중 Desktop+OneDrive가 `--reload` 폭풍을 만들 수 있음 → 동기화 일시 중지 권장.

### 다음
- 추적/테스트 FAB 카피·배치 다듬기.  
- throttle 수치(200m/4초) 실차 체감 후 조정.  
- (선택) 데스크톱 현위치 마커 드래그.  
- Desktop 밖 경로 또는 OneDrive 바탕화면 백업 OFF.

---

## 2026-07-28 — 주행 테스트 탭 수정

### 한 일
- `MapView`: 테스트 ON 시 전면 탭 레이어 + `screenToReal`/`getBounds` 폴백으로 좌표 반영.  
- TMAP `latLng.lat`가 함수/숫자/`_lat` 모두 파싱. `map.addListener("click")` 병행.  
- 테스트 켜면 현재 center/coords로 시드해 마커·원이 바로 보이게.

### 결정
- 테스트 중 지도 팬은 탭 레이어에 가려짐(탭으로 위치 이동이 목적).

### 다음
- 실기에서 탭→원/마커 이동 확인.

---

## 2026-07-28 — GPS 기본 추적 · 시험주행 FAB

### 한 일
- **추적 버튼 제거.** `AppShell`에서 `locateOnce` 후 기본 `startWatch` + `follow`.  
- 반경·목록 origin은 **실 GPS 변경** 또는 **시험주행 탭**일 때만 움직임.  
- FAB: 자동차 아이콘 ↔ `ON` 토글, hover/focus 시 「시험주행」 라벨.  
- 시험주행 OFF 시 GPS watch 재개.

### 결정
- 위치 추적은 opt-in 버튼이 아니라 기본 동작. 시험주행만 명시 토글.

### 다음
- 실기에서 기본 추적·시험주행 탭 확인.

---

## 2026-07-28 — 시험주행 PC 드래그/줌

### 한 일
- PC(`hover`+`pointer: fine`): 전면 탭 레이어 **제거** → TMAP click으로 위치, **드래그·휠 줌 가능**.  
- 모바일(coarse): 기존 탭 레이어 유지.

### 결정
- PC는 지도 제스처 우선, 클릭만 시험 위치.

### 다음
- 모바일에서도 탭/드래그 구분 필요하면 이어서.

---

## 2026-07-28 — 모바일 페이지 줌 방지 · 지도 제스처

### 한 일
- `layout` viewport: `maximumScale=1`, `userScalable=false` (브라우저 화면 확대 차단).  
- `#ev-tmap-map { touch-action: none }` — 핀치/팬을 TMAP으로.  
- 시험주행 전면 탭 레이어 **완전 제거** (PC·모바일 공통: TMAP click으로 위치).

### 결정
- 시험주행 중에도 지도 드래그·핀치 가능. 위치는 탭/클릭.

### 다음
- 폰에서 핀치=지도 줌, 탭=시험 위치 확인.

---

## 2026-07-28 — 시험주행 모바일 탭 복구

### 한 일
- 짧은 **한 손가락 탭**(이동 12px·450ms 이내)만 `screenToReal`로 위치 반영.  
- 핀치/드래그는 `preventDefault` 없이 지도에 그대로 전달. TMAP click은 PC용 유지.

### 결정
- 전면 차단 레이어 없이 탭·줌 병행.

### 다음
- 실기 탭 감도(12px/450ms) 필요 시 조정.

---

## 2026-07-28 — 반경 원 클릭 통과

### 한 일
- `RadiusControl` Circle에 `clickable: false` — 원 안 탭/클릭이 지도·시험주행으로 전달되게 함.  
  (1km 원이 화면을 크게 덮어 클릭이 먹통이던 문제. **의도된 동작 아님**)

### 결정
- 반경 원은 표시 전용. 상호작용은 지도/마커가 받음.

### 다음
- 원 안 시험주행 탭·PC 클릭 재확인.

---

## 2026-07-28 — 시험주행 탭 재수정 (원 숨김 + capture)

### 한 일
- 시험주행 ON 시 **반경 Circle 미표시** (`clickable:false`만으로는 TMAP이 탭을 계속 가로챔).  
- 지도 div에 **capture 단계** pointer/touch 탭 감지 → `screenToReal`.  
- 핀치·드래그는 preventDefault 없음.

### 결정
- 시험 중 원은 숨기고, 반경 API·목록 throttle은 coords 기준으로 유지.

### 다음
- 실기에서 원 자리·빈 지도 모두 탭/클릭 확인.

---

## 2026-07-28 — 회원가입 주소 입력 UI

### 한 일
- `/signup`: **주소**(다음 주소 검색 버튼·readonly, 연동 TODO) + **상세주소** 필드 추가.

### 결정
- Daum Postcode는 `openAddressSearch` stub. BE register 필드는 추후 합의.

### 다음
- 다음 주소 API 연동 · register API에 address 전달.

---

## 2026-07-28 — api/.env·.env.example 정리

### 한 일
- `api/.env`: 섹션·주석 구조 복구(DB/TMAP/수집/Auth). `EV_STATUS_SYNC_ENABLED=false`. 기존 로컬 DB·키 값 유지.
- `api/.env.example`: `EV_CHARGER_API_URL`, `EV_STATUS_*`, JWT 블록 누락분 동기화.

### 결정
- 수집 ON은 한 호스트만; PC 기본은 sync OFF.

### 다음
- 로그인 쓰면 `JWT_SECRET` 로컬에 설정 후 uvicorn 재시작.

---

## 2026-07-28 — User ORM auth 단일화 (DDL 반영)

### 한 일
- `auth/models.py`: `users` DDL 맞춤 (`detail_address`, `user_lat`, `user_lng`, `UserRole`, nickname unique).
- `stations/models.py`: 중복 `User`/`UserRole` 제거 — `Table 'users' already defined` 해소.

### 결정
- `User` 소유는 **auth** 도메인. stations는 `UserFavoriteCharger` 등 FK 문자열만 유지.

### 다음
- signup API에 `detail_address`·좌표 필드 반영 여부 합의.

---

## 2026-07-28 — requirements.txt 충돌 방지 규칙

### 한 일
- Agent/팀 규칙: `api/requirements.txt`는 **새 패키지 맨 아래 append**, 중간 삽입·전체 정렬 금지(conflict 방지). `.cursor/rules/api-files.mdc`, `docs/rules/03_conventions.md`.

### 결정
- 버전만 올릴 때는 해당 줄만 수정. BE 의존성 추가 시 requirements 동시 갱신.

### 다음
- (없음)

---

## 2026-07-28 — 회원가입·로그인 페이지 스크롤

### 한 일
- `/signup`, `/login`: 루트 `body overflow-hidden` 때문에 폼이 잘리던 문제 — 페이지 루트를 `h-dvh overflow-y-auto` 스크롤 컨테이너로 변경.

### 결정
- 지도 앱용 `body` overflow 락은 유지. 인증 페이지만 내부 스크롤.

### 다음
- (없음)

---

## 2026-07-29 — 충전기타입(chgerType) 코드↔이름 매칭

### 한 일
- `web/src/lib/chargerTypes.ts`: KECO 01–10 라벨 맵 + 완속(`02`/`08`) vs 그외 버킷 헬퍼(`stationMatchesTypeFilter` 등).

### 결정
- UI 필터는 완속/그외 이분. 표시명은 공식 코드표 기준. FE 필터용이며 stations 응답에 타입 배열 추가(BE)는 후속.

### 다음
- stations API에 `chgerTypes` 집계 필드 추가 후 StationList/마커에 필터 연결.

---

## 2026-07-29 — stations 응답에 chargerTypes 추가

### 한 일
- `list_stations_near` / `list_stations_viewport`: `GROUP_CONCAT(DISTINCT chger_type)` → `charger_types` 리스트.
- `StationItem.charger_types`, FE `Station.chargerTypes` 타입 반영. SQL CASE 라벨 변환은 하지 않음(FE 매칭).

### 결정
- BE는 원본 코드만. 이름·완속 버킷은 FE `chargerTypes.ts`.

### 다음
- StationList/마커에 완속·그외 필터 UI 연결.

---

## 2026-07-29 — StationDetailCard 충전기 타입 표시

### 한 일
- 상세 카드에 `chargerTypes` → 라벨 칩(완속=초록, 그외=액센트). 타입 없으면 안내 문구.

### 결정
- 표시만; 목록/마커 필터 UI는 후속.

### 다음
- StationList/마커 완속·그외 필터 연결.

---

## 2026-07-29 — MapView 분리 원칙 문서화

### 한 일
- `tmap-sdk-lock.mdc` · `important.md` §2.2 · `01_agent_permissions` · `03_conventions` · `project-overview`: MapView에는 지도 필수만, 그 외 UI/필터는 형제·store·lib로 분리.

### 결정
- 신규 기능은 MapView 본문 확장 금지(조합만). 잠긴 부트스트랩 줄 수 리팩터 금지.

### 다음
- (없음)

---

## 2026-07-29 — 모바일 목록 접기 + 선택 시 센터

### 한 일
- `mobileListOpen` + `selectStation`: 목록/마커 선택 시 시트 접기 · 줌 유지 · `setCenter`만 · follow 해제.
- AppShell 시트 핸들 토글 · FAB/상세는 `--map-sheet-offset` (열림 42dvh / 접힘 peek).
- MapView는 bottom 클래스만 CSS 변수로 (부트스트랩 미변경).

### 결정
- 모바일 기본 UX: 선택 → 지도 중심 + 목록 접어 마커 탭 면적 확보.

### 다음
- 완속 필터 아이콘 토글. 실기기에서 마커 탭·시트 제스처 확인.

---

## 2026-07-29 — 모바일 충전소 탭(히트테스트)

### 한 일
- `StationMarkers`: 반경 Circle이 Marker 탭을 가로채는 TMAP 이슈 → map DOM short-tap → 근처 55m 이내 충전소 `selectStation`.
- selectedId 변경 시 마커 전체 재생성하지 않고 `setIcon`만. touchend/click 병행.

### 결정
- 시험주행(testMode) 중에는 히트테스트 스킵.

### 다음
- 실기기에서 마커 탭 재확인.

---

## 2026-07-29 — UI 폰트 Noto Sans KR

### 한 일
- `layout.tsx`: Manrope / Plus Jakarta Sans → `Noto_Sans_KR` (`--font-sans`, display=swap).
- `globals.css`: `--font-display` = `--font-sans`. 마커 canvas도 Noto 우선.

### 결정
- TMAP 베이스맵 라벨 폰트는 변경하지 않음(SDK/타일).

### 다음
- (없음)

---

## 2026-07-29 — 완속 필터(includeSlow) 완성

### 한 일
- `mapStore.includeSlow` 기본 false(그외만). `filterStationsBySlowInclude`로 List/Markers 공통 필터.
- `SlowChargeFilterFab`: 아이콘 토글 + 탭 시 「완속 포함/숨김」. MapView FAB 스택에 조합만.
- 완속 끄면 선택 중이던 완속-only 충전소는 선택 해제.

### 결정
- 타입 미상(`chargerTypes` 없음)은 필터에서 숨기지 않음.

### 다음
- 실기기에서 토글·목록·마커 동기 확인.

---

## 2026-07-29 — 가용 합계(마커) + 버킷 분해(상세)

### 한 일
- BE stations: `availableCount`(전체) 유지 + `availableCountOther` / `availableCountSlow` 집계(완속 02/08, null 타입→other).
- FE: 마커·리스트는 합계만. 상세 카드는 혼합소만 그외/완속 대기 분리 표기.
- `stations_api.md` 필드 설명 갱신.

### 결정
- 완속 숨김 시 완속-only는 목록에서 제외되므로, 분해 UI는 혼합소에만 필요.
- 마커 가시성 위해 혼합소도 합계 숫자 유지.

### 다음
- 혼합 충전소 탭 시 상세 숫자와 DB status 대조.

---

## 2026-07-29 — 회원가입 주소 검색 모달

### 한 일
- `AddressSearchModal`: 앱 토큰 UI + `searchTmapPlaces`(BE places) 연동. 결과 목록 name/address, 디바운스·로딩·빈결과.
- signup 주소 필드는 모달 `onSelect`로 채움.

### 결정
- BE가 내려주는 필드는 id/name/address/lat/lng만 사용(TMAP 원본의 일부). count 최대 10.

### 다음
- 필요 시 BE에서 도로명·지번 등 추가 필드 매핑 검토.

---

## 2026-07-29 — 로그인 화면 id/pw 입력 UI

### 한 일
- `/login`: 이메일·비밀번호 입력 + 로그인 버튼 폼 추가 (signup과 동일 필드 스타일).
- `onSubmit`은 preventDefault + FormData 추출만 (API 연동은 사용자가 직접).

### 결정
- 로컬 로그인 폼을 상단, 소셜·회원가입은 그 아래. 가입과 동일하게 `userId` = 이메일.

### 다음
- `POST /api/v1/auth/login` 연동 및 토큰 저장·returnUrl 이동.

---

## 2026-07-29 — 로그인 소셜 버튼 UI 개선

### 한 일
- 카카오/구글/네이버: 브랜드 SVG 아이콘 + 좌측 원형 뱃지, 호버·프레스 피드백.
- 카피: 「~로 계속하기」, 구분선 문구 「소셜 계정으로 계속」.

### 결정
- 아이콘은 페이지 인라인 SVG (외부 이미지/폰트 의존 없음).

### 다음
- (없음)

---

## 2026-07-29 — 로컬 로그인 JWT 저장·이동

### 한 일
- `/login` 성공 시 `localStorage.accessToken` 저장, authStore 유저·포인트 hydrate, `returnUrl`(기본 `/map`)로 `router.replace`.

### 결정
- BE camelCase `accessToken` 사용. Bearer는 이후 API 호출 헤더에서 읽음.

### 다음
- fetch 공통 Authorization 헤더 / `fetchMe` 연동.

---

## 2026-07-29 — 로그인 성공 후 hard redirect

### 한 일
- 로그인 성공 시 `router.replace` → `window.location.assign(returnUrl|/map)` 로 변경 (소프트 네비가 안 먹는 경우 대비).

### 결정
- 인증 직후 이동은 hard navigation 우선.

### 다음
- (없음)

---

## 2026-07-29 — 로그인 후 TopBar 로그아웃 표시

### 한 일
- `authStore.fetchMe`: localStorage Bearer → `GET /api/v1/auth/me` hydrate.
- `logout`: 토큰 삭제 + store clear (+ BE logout 호출).
- `/map` `handlePostLoginLanding`에서 fetchMe 호출 → TopBar가 닉네임/로그아웃으로 전환.

### 결정
- TopBar UI는 기존 `user ? 로그아웃 : 로그인` 유지. 문제는 hard redirect 후 store 소실 → /me로 복원.

### 다음
- (없음)

---

## 2026-07-29 — 로그인 에러 UI·모바일 압축 레이아웃

### 한 일
- 로그인 실패 시 `error`를 폼 아래 alert로 표시 (기존엔 set만 하고 렌더 누락).
- 모바일: 패딩·타이틀·버튼·간격 축소, 설명문 숨김, 회원가입을 하단 고정에 가깝게 배치해 한 화면에 맞춤.

### 결정
- BE `id 또는 password 오류` → FE에서 사용자용 문구로 치환.

### 다음
- (없음)

---

## 2026-07-29 — Auth /me FE 규칙 문서화

### 한 일
- `docs/rules/06_auth_me.md` + `.cursor/rules/auth-me.mdc` 추가 (Bearer·hydrate·`user:null` 시 토큰 삭제).
- `docs/rules/README.md`·`03_conventions.md`·`project-overview.mdc`에 링크.

### 결정
- `/me`는 optional auth(대개 200+user null). 401만으로 비로그인 판단하지 않음.

### 다음
- 커밋 시 `web/docs/rules`·`api/docs/rules` 동기화 여부 팀 관행 따름.

---

## 2026-07-29 — 모바일 페이지 줌 방지 규칙

### 한 일
- `docs/rules/07_mobile_viewport_zoom.md` + `.cursor/rules/mobile-viewport-zoom.mdc` 추가.
- 확대 후 viewport로 축소 불가 → 로그인 포함 전역 가드, 지도만 `#ev-tmap-map` 핀치. 새 페이지 체크리스트 명시.

### 결정
- `touch-action: manipulation` 사용 지양(핀치 페이지 줌 허용). 전역 pan + DisableBrowserZoom 유지.

### 다음
- (없음)

---

## 2026-07-29 — 완속 필터에 맞춰 가용 대수 표시

### 한 일
- `availableCountForSlowFilter`: 완속 제외 시 `availableCountOther`, 포함 시 `availableCount`.
- StationList·StationMarkers가 위 헬퍼로 「충전가능」/마커 숫자 표시.

### 결정
- 목록에 보이는 충전소와 가용 숫자 기준을 동일하게 맞춤(기본=그외만).

### 다음
- 혼합소에서 완속 토글 시 목록·마커 숫자 변화 실기 확인.

---

## 2026-07-29 — 마커 총대수도 완속 필터 반영 (`chargerTotalOther`)

### 한 일
- BE: `_TOTAL_SQL` — `charger_total` + `charger_total_other`(02/08 제외, 공란→other). near/viewport 공통.
- FE: `chargerTotalForSlowFilter` → 마커 `가용/총` 분모. `chargerTotalSlow` 없음(필요 시 total−other).
- `stations_api.md` / `backendguide.md` 반영.

### 결정
- 총대수는 가용과 달리 null 버킷이 없어 total+other만. slow는 파생.

### 다음
- 혼합소에서 완속 토글 시 마커 분모 변화 실기 확인.

---

## 2026-07-29 — `backendguide.md` 완속·총대수 계약 보강

### 한 일
- S5 응답 필드·`includeSlow` 표, §1.3~1.3.2(가용 3버킷·`_TOTAL_SQL`·BE 비필터), §6·7.1·실수 목록·멘탈 모델 갱신.

### 결정
- 로컬 가이드가 stations 가용/총 + FE 토글 분계의 SSOT 보조.

### 다음
- (없음)

---

## 2026-07-29 — 메뉴·IconRail 아이콘 교체

### 한 일
- compact「메뉴」텍스트 필 → 사이드레일 글리프 FAB(열림=사각 X). 지도 FAB 사이즈와 통일.
- IconRail: 핀·북마크·P카드·슬라이더 + 충전기 마크(번개 제거). 활성 인디케이터 각진 바.

### 결정
- 기본 Lucide식(접힌지도·별·$·방사 톱니·번개)에서 제품 톤으로 단순화.

### 다음
- 폰에서 메뉴 토글·레일 아이콘 가독성 확인.

---

## 기록 규칙

1. 날짜 헤더(`## YYYY-MM-DD — 제목`)로 추가.
2. 한 일 / 결정 / 다음만 짧게. 키·토큰·DB 비번·실 `.env` 값 금지.
3. Agent가 의미 있는 구현을 마치면 이 파일에 한 블록 append.
4. Git 올릴 때 `web/docs/teamdeveloper.md`, `api/docs/teamdeveloper.md` 동기화.
5. 새 블록 추가 시 위 **요약** 표도 최신화. 온보딩 섹션이 바뀌면 상단도 함께 수정.

## 2026-07-29 — 모바일 충전소 마커 탭 성능 최적화

### 한 일
- `StationMarkers.tsx`: `buildCircleIconUrl` 결과를 `label|fill|selected` 키로 모듈 레벨 Map 캐시 추가 → 동일 상태 마커 반복 canvas 생성 제거
- `StationMarkers.tsx`: `selectedId` 변경 시 전체 마커 순회 대신 이전 선택 마커 + 새 선택 마커 **2개만** 아이콘 업데이트 (`prevSelectedIdRef` 추가)
- `mapStore.ts`: `selectStation`에서 `mobileListOpen`이 이미 닫혀있을 때 불필요한 `map.resize()` 호출 제거 → 시트가 열려있었을 때만 resize

### 결정
- 캐시는 모듈 생명주기 동안 유지 (앱 새로고침 시 초기화). 마커 종류 수가 적어 메모리 문제 없음.
- `includeSlow` 변경 시에는 전체 목록 변경이므로 기존 `[map, visible]` effect가 전체 재생성 → 문제 없음.

### 다음
- 마커 탭 반응성 추가 개선 여지 있음 (TMAP screenToReal 좌표 오차)

## 2026-07-30 — 모바일 목록 시트 3단 + 헤더 압축

### 한 일
- `mapStore`: `mobileListOpen` → `mobileSheetSnap` (`peek` | `half` | `full`). `setMobileListOpen`은 half/peek 호환 유지.
- `AppShell`: 시트 높이 `2.75rem` / `42dvh` / `90dvh`. 핸들 탭 순환, 스와이프 up/down 한 단계.
- `StationList`: 모바일 `compactHeader` — Nearby 제거, 한 줄 제목+메타. 사이드 패널도 헤더 약간 축소.

### 결정
- 큰 기종에서도 42dvh+큰 헤더면 2칸만 보여 답답 → 최대화(90dvh) + 헤더 압축.
- 선택 시 snap → peek (기존 접기와 동일 의도).

### 다음
- 실기기에서 half/full 체감·FAB offset 확인. 위치 모드(현위치 setFollow 등)는 별도.

## 2026-07-30 — 목록 시트 스와이프 (dragEnd 방식)

### 한 일
- 최소|중간|최대 세그먼트 제거. 탭=peek↔half 토글, full은 스와이프.
- 제스처: move 중 즉시 snap 금지 → pointerup에서 offset(50) + velocity(400px/s)로 판정 (병원 MobileBottomSheet/framer 참고).
- `setPointerCapture` + `touch-none`으로 핸들 밖에서도 드래그 유지.

### 결정
- framer-motion 미도입(의존성 추가 보류). 동일 dragEnd 로직만 이식.
- 사용자 UX: 토글 + 스와이프가 세그먼트보다 자연스러움.

### 다음
- 실기기에서 스와이프 감도 확인. 필요 시 framer drag 도입.

## 2026-07-30 — 목록 시트 드래그 따라가기 (transform)

### 한 일
- `MobileStationSheet`: height 애니메이션 제거 → `translate3d` + 드래그 중 손가락 추종, 놓으면 340ms ease snap.
- FAB offset은 드래그 중에도 `--map-sheet-offset` px로 갱신.

### 결정
- 끊김 원인 = 놓을 때만 높이 점프. 병원 framer 시트와 같이 드래그 중 시각 피드백 필요.

### 다음
- 체감 부족 시 framer-motion spring 검토.

## 2026-07-30 — 모바일 가이드 `mobile.md` (로컬)

### 한 일
- 워크스페이스 상위 `mobile.md` 추가: compact·바텀시트 snap·줌·FAB·Circle·파일 인덱스 (git 밖).

### 결정
- 모바일 전용 설정은 `mapguides`와 분리해 `mobile.md`에 모은다.

### 다음
- (없음)

## 2026-07-30 — IconRail 내 차량 메뉴(UI)

### 한 일
- `IconRail`: 설정 위에 「내 차량」 네비 항목 추가(아이콘만, 화면/API 미연동).

### 결정
- 설정은 유지. 차량 등록·포트 필터 진입은 이후 「내 차량」에 연결.

### 다음
- 차량 등록 UI·cars API·포트 기반 충전소 필터.

## 2026-07-30 — FE `Car` / `CarModel` 타입

### 한 일
- `web/src/types/car.ts`: `cars` DDL에 맞춘 camelCase 타입 (`ChargingPort`, `Car`, `CarModel`).

### 결정
- id는 auth와 같이 string. 유효 포트 = `chargingPort ?? carModel.chargingPort`.

### 다음
- `carStore`·`CarPanel` 연동.

## 2026-07-30 — carStore / CarPanel 껍질

### 한 일
- `carStore`: cars·primaryCar·`filterByCarPort`(기본 true)·`effectiveChargingPort`.
- `CarPanel`: 빈 상태 + 포트 필터 토글 UI (레일 연결 전).

### 결정
- persist 미사용(mapStore와 동일). API 연동 전 로컬 state만.

### 다음
- IconRail `car` 탭 → AppShell 패널에 CarPanel 표시.

## 2026-07-30 — IconRail ↔ 사이드 패널 네비 연결

### 한 일
- `NavId`를 `car`로 통일·export. `IconRail`에 `onSelect` + 클릭 핸들러.
- `AppShell`: `activeNav` 로컬 state로 `StationList` / `CarPanel` / `UnimplementedHint` 분기. `listPanelOpen` 재사용.

### 결정
- 패널 open은 store가 아니라 AppShell. 모바일 시트 연동은 후속.

### 다음
- 모바일에서 car 패널 표시. CarRegisterSheet·포트 필터 연동.

## 2026-07-30 — 차량 포트 ↔ chgerType 매핑

### 한 일
- `chargerTypes.ts`: `PORT_TO_CHGER_TYPE_CODES` (CCS1/CHADEMO/NACS) + `chgerCodesForChargingPort` + `stationMatchesCarPort`.

### 결정
- 어댑터 없음: NACS=09/10만, CCS에 09 미포함. 미분류/포트 없음은 통과.
- `ChargerTypeBucket`(완속)과 축 분리.

### 다음
- List/Markers에 포트 필터 적용 + CarPanel 임시 토글.

## 2026-07-30 — CarPanel 임시 포트 버튼

### 한 일
- `CarPanel`: CCS/CHAdeMO/NACS 버튼 → `buildTempCar` 후 `setCars` + 필터 ON. 지우기·기존 토글 유지.

### 결정
- 등록 API 전: 패널에서만 가짜 `Car`를 store에 넣음. DB 조회 없음.

### 다음
- StationMarkers visible에 포트 필터 맞추기(List는 연결됨). 실기 확인.

## 2026-07-30 — 포트 필터 빈 결과 안내

### 한 일
- `StationList`: 내 차 포트 필터로 0건일 때 안내 + 「전체 보기」. NACS는 “매우 적음” 문구(숫자 고정보다 정성).
- `CarPanel`: NACS 선택 시 시내·공공 NACS 희소 안내.

### 결정
- DB 건수(예: 5개)를 UI에 하드코딩하지 않음 — 수집·지역 변동에 바로 거짓이 됨.

### 다음
- (선택) 지도 칩·등록 UI에도 동일 카피 재사용.

## 2026-07-30 — 모바일 시트에 네비 패널 연결

### 한 일
- 모바일(`md` 미만) 사이드 패널은 원래 `hidden` — CarPanel이 안 보이던 것.
- `MobileStationSheet`에 `activeNav` 전달: 지도=StationList, 내 차량=CarPanel 등.
- 레일에서 항목 선택 시 시트를 `half`로 펼침.

### 결정
- 데스크톱=왼쪽 패널 교체, 모바일=하단 시트 내용 교체 (지도는 유지).

### 다음
- 실기기에서 메뉴 FAB → 내 차량 → 포트 필터 확인.

## 2026-07-30 — 모바일 하단 네비 (레일·메뉴 FAB 제거)

### 한 일
- `MobileBottomNav`: compact 전용 하단 탭 바 (`MAIN_NAV` 공유).
- `AppShell`: PC만 `IconRail`. 모바일 왼쪽 레일·메뉴 on/off FAB 제거. 지도 영역 아래 하단 네비.
- 탭 선택: 지도→시트 peek, 그 외→half + 시트 내용 교체.

### 결정
- 모바일 주 메뉴는 상시 하단. 토글 FAB 불필요.

### 다음
- 실기기에서 하단 네비·시트·지도 FAB 겹침 확인.

## 2026-07-31 — 내 차량 포트 필터 노출 (모바일)

### 한 일
- CarPanel: 「내 차량 포트만 보기」를 패널 상단으로 이동 (시트 half에서 잘림 방지). 포트 없을 때 체크 비활성.
- CarPortFilterFab: 완속 FAB 옆에 지도 토글 추가. 임시/등록 차량 포트가 있을 때만 표시, 시트 펼침 없이 on/off.
- MapView: FAB 조합만 (부트스트랩/반경 미변경).

### 결정
- 포트 필터는 지도 표면에서도 조작. 차량 선택·등록 UI는 패널 유지.

### 다음
- 실기기에서 포트 선택 → FAB 노출 → peek에서도 토글·목록/마커 반영 확인.

## 2026-07-31 — CarPanel 컴팩트 (NACS 잘림)

### 한 일
- CarPanel: 포트 세로 버튼 → 가로 칩, 여백·카피 축소. NACS 안내 한 줄. 스크롤 허용.

### 결정
- 시트 half에서 필터·포트·NACS가 한눈에 들어오게 세로 밀도 우선.

### 다음
- 실기기 half 시트에서 NACS 선택 시 안내 문구 잘림 여부 확인.

## 2026-07-31 — 지도 드래그 마우스 붙음/떨림 (시험주행 OFF)

### 한 일
- 원인: 기본 follow + GPS setCenter, 그리고 PC 반경 Circle destroy/recreate가 드래그 중 TMAP pan과 충돌.
- lib/map/mapGesture.ts: pointerdown~up(+450ms) 제스처 락.
- AppShell: watch는 유지, 기본 `follow=false` (현위치 버튼만 chase).
- MapView: 제스처 중 follow/center sync/내 위치 마커 갱신 스킵.
- RadiusControl: 제스처 중 원 재생성·cleanup destroy 스킵 (줌 프리셋 로직 미변경).
- locationStore watch: 제스처 중 coords 미갱신.

### 결정
- watching ≠ follow. 카메라 추적은 현위치 탭 후에만.

### 다음
- PC에서 드래그·클릭·반경 원 표시 상태에서 떨림 재발 여부 확인.

## 2026-07-31 — 문서 등급·지도 가이드 통합·mobile 최신화

### 한 일
- mapguide.md + mapguides.md → **mapguides.md 단일본** (현재 follow/제스처/차량 FAB 반영). mapguide.md는 리다이렉트만.
- mobile.md 최신화: MobileBottomNav, 메뉴 FAB 제거, CarPanel/FAB, mapGesture, follow 기본 OFF.
- api/docs/02_BACKEND_GUIDE.md **OBSOLETE** 헤더. BACKEND_GUILD.md·backendguide.md에 S0 우선·폐기 안내.
- docs/rules/README.md에 S0/S1/S2/S3 등급표.

### 결정
- 사용자가 둔 docs/rules·important·합의·.cursor/rules가 **정본(S0)**. 해설 가이드는 S0와 충돌 시 가이드를 고친다.

### 다음
- BE 리포에 obsolete/GUILD 변경 커밋은 담당자 확인 후. 루트 md는 로컬 공유.
## 2026-07-31 — teamdeveloper UTF-8 append 규칙

### 한 일
- docs/rules/04_teamdeveloper_log.md: Windows/Agent UTF-8 필수, PowerShell Add-Content 금지, Python/Out-File -Encoding utf8 권장.
- .cursor/rules/teamdeveloper-log.mdc·docs/rules/README.md에 동일 안내.

### 결정
- 한글 md(특히 teamdeveloper)는 UTF-8만. CP949 append로 GitHub 깨짐 재발 방지.

### 다음
- (없음)
## 2026-07-31 — status sync 로그에 KST 시각

### 한 일
- api/app/domains/stations/sync.py: sync 로거 전용 Formatter에 %(asctime)s (KST) 적용. 메시지 본문에 datetime을 넣지 않음.
- 포맷: YYYY-MM-DD HH:MM:SS LEVEL [status-sync] .... --reload 시 핸들러 중복 방지.

### 결정
- status sync 관련 로그는 전부 시간 표시. 앱 전역 logging 개편은 하지 않음.

### 다음
- 터미널에서 FK 스킵·upsert 로그에 시각이 붙는지 확인.

## 2026-07-31 — 장소 검색 요약 바 + 길찾기 스텁

### 한 일
- 
outeStore: 도착지 preview · startDirections(출발=현위치). FEATURES.tmapRouteFind=false.
- PlaceSummaryBar: 검색 선택 후 하단 요약(이름·주소·길찾기·닫기) + 목적지 핀. 결과 행마다 버튼 없음.
- MapSearchBar 선택 시 destination 설정·시트 peek·충전소 선택 해제·줌 18.
- StationDetailCard 길찾기 → 동일 startDirections. 검색 요약과 상세는 동시에 안 띄움.
- MapView는 조합만 (PlaceSummaryBar import). TMAP SDK/RadiusControl 미변경.

### 결정
- 길찾기 CTA는 목록 행이 아니라 선택 후 요약 바/상세 카드. 경로 API·폴리라인은 이후 BE 연동.

### 다음
- BE TMAP 경로 프록시 + 폴리라인/ETA UI. 	mapRouteFind true.

## 2026-07-31 — 검색 중 FAB·시트 가림 수정

### 한 일
- 검색 UI 활성 시 모바일 시트를 peek로 접고, 좌측 FAB/반경 컨트롤 숨김 (mapStore.searchUiOpen).
- 검색 오버레이 z-index 상향. 목록 half/full + 키보드로 FAB이 검색창을 가리던 문제 대응.

### 결정
- 검색 중에는 시트·FAB보다 검색 입력 우선. 닫기/바깥 탭 후 FAB 복귀.

### 다음
- 실기기에서 검색 열기·키보드·닫기 동선 확인.

## 2026-07-31 — StationDetailCard ETA + 길찾기 모드 레이아웃

### 한 일
- StationDetailCard: routeStore distanceM/durationSec/status 연동. 이 충전소 길찾기 시 ETA(분·경로 km) 표시.
- 길찾기 모드(loading/ready/error): 카드 패딩·min-height 확장, 충전기 타입/직선 km 대신 정사각 ETA 타일 2칸. 버튼 「다시 길찾기」.
- PlaceSummaryBar: ETA 문구·loading 정리, unimplemented hint 복구. 깨진 WIP import 제거.

### 결정
- 카드 전체 aspect-square 강제 대신, 길찾기 모드에서 ETA 타일만 aspect-square + 카드 한 단 확장 (모바일·웹 공통). 지도 가림 최소화.

### 다음
- 실시간 재경로 throttle (자유주행 ON 후 위치 이동 시 km·분·선 갱신).

## 2026-07-31 — 충전소 선택 시 활성 길찾기 유지

### 한 일
- mapStore.selectStation: status가 loading/ready일 때 clearDestination 호출 안 함 (경로·ETA·폴리라인 유지).
- preview/idle/error일 때만 장소검색 요약 destination 정리 (상세와 상호배타).

### 결정
- 자유주행 중 TMAP Marker click은 그대로 동작(DOM nearest-hit만 testMode 가드). 충전소 탭 ≠ 길찾기 해제.
- 길찾기 해제는 × / clearDestination 명시 동작에만.

### 다음
- 실시간 재경로 throttle.

## 2026-07-31 — 경로 취소 버튼

### 한 일
- StationDetailCard: 길찾기 모드에 「경로 취소」+「다시 길찾기」. 다른 충전소 열람 중에도 활성 경로면 「경로 중 · 이름 / 경로 취소」 스트립.
- PlaceSummaryBar: loading/ready 시 「경로 취소」 버튼. ×도 clearDestination.

### 결정
- 길찾기 해제는 명시적 취소만 (충전소 탭으로는 안 지움).

### 다음
- 실시간 재경로 throttle.

## 2026-07-31 — 자유주행 탭 시 현위치 마커 고정 수정

### 한 일
- MapView: coords→현위치 Marker 이펙트에서 isMapGestureActive 가드 제거. 탭 중 setTestCoords 후에도 setPosition 반영.
- createMap / SDK 로드 / RadiusControl 카메라·원 가드는 변경 없음 (카메라 chase만 제스처 중 스킵 유지).

### 결정
- 마커 setPosition은 팬 전투 대상이 아님. 제스처 hold(~450ms) 동안 스킵하면 coords가 안 바뀌어 마커가 영구 고정됨 → 주행테스트 체감 저하.

### 다음
- 자유주행 ON → 지도 탭 → 마커 이동 확인. 이후 재경로 throttle.

## 2026-07-31 — 실시간 재경로 throttle

### 한 일
- routeStore: maybeRefreshRoute — status=ready일 때 현위치 기준 **150m 또는 4초**(미만은 trailing). silent refresh(구 path/ETA 유지, 실패 시 유지).
- RouteLiveRefresh: coords 구독 → maybeRefreshRoute. MapView는 조합만.
- startDirections는 기존처럼 loading UI. clearDestination 시 in-flight 무효화.

### 결정
- stations throttle(200m/4초)과 유사, 주행테스트 체감용 150m. 수치 실차 후 조정 가능.
- 1단계 길찾기(출발=현위치·폴리라인·ETA·취소·자유주행 연동 throttle) 골격 완료. 턴바이턴/음성/이탈 재탐색 UX는 이후.

### 다음
- 자유주행 ON → 길찾기 → 탭 이동 → km·분·선 갱신 확인.

## 2026-07-31 — mapguides.md 길찾기 1단계 반영

### 한 일
- 루트 mapguides.md: routeStore·ETA·Polyline·LiveRefresh throttle·경로 취소·selectStation 유지·마커 제스처 가드 수정·시나리오 G–I 갱신.

### 결정
- S2 해설은 mapguides.md 단일. mapguide.md는 리다이렉트 유지.

### 다음
- 실기기에서 자유주행+재경로 체감 확인.

## 2026-08-03 — 자유주행 중 충전소 선택 잠금 + 길찾기 UI 유지

### 한 일
- 자유주행(testMode) ON: selectStation / Marker click / 목록 행으로 충전소 선택 불가(활성 경로 목적지 복원만 예외).
- StationDetailCard: 다른 충전소 열람 시 「경로 중」 스트립에 펼치기(목적지 선택 복원).
- PlaceSummaryBar: 길찾기 loading/ready일 때 StationDetailCard와 같은 ETA 타일 레이아웃 유지(카드 × 후에도 안 줄어듦).

### 결정
- 자유주행 핵심 제스처=맵 탭 위치 지정. 충전소·상세 선택은 충돌 원인이라 잠금. 반경/OFF/지도 팬·핀치는 유지.
- 길찾기 축소 체감은 (1) 타 충전소 탭 → 경로 중 스트립 (2) 상세 × → 얇은 요약바. 스트립 펼치기 + 요약바 ETA 확장으로 대응.

### 다음
- 실기기에서 자유주행+길찾기 탭 이동 시 충전소 안 열림·ETA 유지 확인.

## 2026-08-03 — 자유주행: 목록 선택은 유지 (마커만 잠금)

### 한 일
- selectStation / StationList 잠금 롤백. 자유주행 중에도 목록·시트로 충전소 선택·길찾기 가능.
- 맵 Marker click / nearest-hit만 testMode에서 무시 (맵 탭=가짜 현위치 충돌 방지).
- 길찾기 ETA 유지·「경로 중 펼치기」는 그대로.

### 결정
- 잠글 대상은 지도 위 마커 탭뿐. 리스트는 의도적 선택이므로 연다.

### 다음
- 자유주행: 목록으로 목적지 → 길찾기 → 맵 탭 이동 시나리오 확인.

## 2026-08-03 — 길찾기 중 버튼 카피: 경로 취소 → 안내종료

### 한 일
- StationDetailCard / PlaceSummaryBar: 활성 경로(loading·ready) 종료 CTA를 「안내종료」로 통일.

### 결정
- ETA 1분 이하 등 조건부 문구는 안 씀(0분 반올림·짧은 km에서만 바뀌면 체감 차이 없고 기준만 복잡). 안내 중엔 항상 안내종료.

### 다음
- 없음(카피만).

## 2026-08-03 — 현위치/도착 마커 형태 구분

### 한 일
- lib/tmap/roleMarkers.ts: 현위치=파란 GPS 원, 도착=빨간 핀(SVG data URL + MarkerImage).
- MapView 현위치 Marker·PlaceSummaryBar 검색 도착 Marker에 적용. loadSdk/createMap/RadiusControl 미변경.

### 결정
- 색만 다른 핀보다 원 vs 핀이 출발/도착 구분에 유리. 충전소 길찾기는 기존 충전소 마커 유지(검색 도착 핀만 변경).

### 다음
- 길찾기 중 충전소 목적지에 도착 핀 오버레이가 필요하면 별도.

## 2026-08-03 — ev_charger_info 고정 컬럼 확장 / output_now 정리

### 한 일
- `EvChargerInfo` ORM에 getChargerInfo 고정 필드 풀세트 반영 (`output`, `busi_nm`, `use_time`, `parking_free` 등).
- `EvChargerStatus`에서 `output_now` 제거. status sync는 `charger_status` + `last_updated`만 upsert.
- 합의 문서 §5·backendguide 테이블 요약 갱신.

### 결정
- 저장은 info 풀세트, API/화면은 필요한 컬럼만 노출.
- 정격 출력(kW) = `ev_charger_info.output`. status의 `output_now`는 의미상 스펙이라 폐기.
- 충전요금(원/kWh)은 원본 API에 없음 — 스키마에 넣지 않음.

### 다음
- DB에 ALTER로 info 컬럼 추가 + (선택) `output_now` DROP. 기존 DB에 `year`만 있으면 `install_year`와 매핑 확인.
- info 적재/보강 시 `output` 등 채우기. 상세 API에서 쓸 필드만 SELECT.

## 2026-08-03 — 길찾기 시 Directions 카드 유지

### 한 일
- routeStore startDirections: 시트 peek + 목적지 stationId면 selectedId 복원(없으면 null → PlaceSummaryBar).
- StationDetailCard ×: 경로 중(loading/ready)에는 목록 half를 열지 않고 peek만 — 요약바 Directions 카드가 가려지지 않게.

### 결정
- 자유주행(찍은 출발) + 길찾기는 막지 않음. 카드만 항상 보이게 해서 같은 흐름을 씀.
- 출발=locationStore.coords(실GPS·시험좌표 공통).

### 다음
- 실기기: 자유주행 탭 → 목록/검색 목적지 → 길찾기 → ETA 카드 유지·× 후 요약바 확인.

## 2026-08-04 — 즐겨찾기 별 버튼 (목록·상세)

### 한 일
- FavoriteStarButton + avoriteStore(stationId 로컬 토글) 추가.
- StationList 행 우측·StationDetailCard 헤더(× 왼쪽)에 별 버튼 연결. 목록/상세 동기화.

### 결정
- API·로그인 게이트는 아직 없음. UI 토글만. 즐겨찾기 탭 목록은 Unimplemented 유지.

### 다음
- favorites API + auth 연동, 즐겨찾기 탭에 저장된 목록 표시.
## 2026-08-04 — 포인트 지갑·거래·결제 테이블 생성

### 한 일
- DB에 포인트/결제 최소 스키마 3테이블 생성: point_wallets, point_transactions, payments.
- 합의 문서의 point_wallets / ledger / payments(B안) 방향을 구체 DDL로 확정.

### 스키마 요약

#### 1) point_wallets (잔액 캐시)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| user_id | BIGINT PK | users.id FK (ON DELETE RESTRICT) |
| balance | INT NOT NULL DEFAULT 0 | 포인트 잔액 캐시 (CHECK balance >= 0) |
| version | INT NOT NULL DEFAULT 0 | 낙관적 락용 버전 |
| created_at / updated_at | DATETIME | updated_at는 ON UPDATE |

- PK = user_id (유저당 지갑 1개).

#### 2) point_transactions (원장·거래 내역)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT AI PK | |
| wallet_id | BIGINT NOT NULL | point_wallets.user_id FK |
| type | ENUM(charge,use,refund,expire,bonus,adjust) | 부호는 type으로 판단 |
| amount | INT NOT NULL | 항상 양수 (CHECK amount > 0) |
| balance_after | INT NOT NULL | 거래 직후 잔액 스냅샷 |
| ref_type | ENUM(payment,usage_order,admin,promo) NULL | 다형성 참조 타입 |
| ref_id | BIGINT NULL | 다형성 FK(DB 미보장, 앱 검증) |
| idempotency_key | VARCHAR(100) NULL UNIQUE | 중복 적재 방지 |
| memo | VARCHAR(255) NULL | |
| created_at | DATETIME | |

- 인덱스: (wallet_id, created_at), (ref_type, ref_id).
- 
ef_type/
ef_id는 둘 다 NULL이거나 둘 다 NOT NULL (CHECK).

#### 3) payments (실결제·충전 주문)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT AI PK | |
| user_id | BIGINT NOT NULL | users.id FK |
| amount_krw | INT NOT NULL | 실결제 원 (> 0) |
| points_granted | INT NOT NULL | 지급 포인트(보너스 포함 가능) |
| bonus_points | INT NOT NULL DEFAULT 0 | 보너스분 (<= points_granted) |
| status | ENUM(pending,paid,failed,cancelled,refunded) | 기본 pending |
| pg_provider | ENUM(inicis,test,toss) NULL | |
| pg_tid | VARCHAR(100) NULL | PG 거래번호(승인 후) |
| idempotency_key | VARCHAR(64) NULL UNIQUE | |
| paid_at | DATETIME NULL | |
| created_at / updated_at | DATETIME | |

- UNIQUE (pg_provider, pg_tid), 인덱스 (user_id, created_at).

### 관계
`	ext
users 1 ── 1 point_wallets
point_wallets 1 ── N point_transactions
users 1 ── N payments
payments(paid) ──(앱)──> point_transactions(type=charge, ref_type=payment)
`

### 결정
- 테이블명은 합의 초안의 point_ledger 대신 **point_transactions** 사용.
- 잔액은 point_wallets.balance 캐시 + 거래마다 alance_after 스냅샷.
- mount는 항상 양수, 증감은 	ype으로 표현.
- PG는 	est 포함(토이 A/B안 모두 수용). 상용 정산 범위는 여전히 제외.
- 시크릿·PG 실키는 문서/리포에 넣지 않음.

### 다음
- BE: wallet 잔액 조회 / 테스트 충전(A안) 또는 PG 콜백(B안) API.
- 충전 성공 시 payments → point_transactions → point_wallets.balance 트랜잭션 묶기.
- ORM 모델·OpenAPI 계약 문서화. FE 잔액·충전·내역 UI 연동.

## 2026-08-04 — 검색 preview 충전소조회

### 한 일
- PlaceSummaryBar: 검색 직후(status=preview)에만 「충전소조회」 버튼 (길찾기 옆). 길찾기 loading/ready/error 이후엔 숨김.
- mapStore stationsAnchor: 도착지 lat/lng로 목록·마커 fetch. AppShell이 anchor 우선, 없으면 현위치.
- 클릭 시 시트 half·지도 중심 도착지. setDestination / clearDestination / startDirections 시 anchor 해제.

### 결정
- 라벨은 짧은 「충전소조회」(aria는 도착지 주변 충전소 조회). RadiusControl(원)은 TMAP 잠금이라 미변경 — 목록/마커만 도착지 기준.

### 다음
- 반경 원을 도착지 앵커에 맞출지(잠금 해제 승인 후) 검토.

## 2026-08-04 — PlaceSummaryBar CTA 레이아웃

### 한 일
- preview: 충전소조회를 주소 아래 작은 chip으로 이동(보조). 길찾기는 flex-1 제거 → 오른쪽 내용 폭 pill.
- 길찾기 행은 나중에 충전확률 버튼을 shrink-0로 옆 추가할 자리만 남김.

### 결정
- 충전소조회=단순 주변 조회 보조. 메인 CTA는 길찾기(+추후 충전확률).

### 다음
- 웹에서 preview 카드 밀도·탭 영역 확인.

## 2026-08-04 — RadiusControl 도착지 stationsAnchor 원점

### 한 일
- RadiusControl: 원·1/2/3 카메라 중심 = stationsAnchor → coords → mapCenter.
- 고정 줌 프리셋·탭 시에만 카메라·fitBounds 금지는 유지. important.md §2.3 갱신.

### 결정
- 검색「주변」조회 중 반경 변경 시 현위치로 점프하지 않음. 목록(AppShell)과 지도 원점 일치.

### 다음
- 데스크톱: 주변 → 2/3km 탭 시 도착지 유지·zoom만 변경 확인. (모바일은 원 미표시·기존 early return 유지)

## 2026-08-04 — 검색·도착지 주변 조회·반경·선택 버그 (통합)

### 한 일
- **MapSearchBar**: 장소 선택 후 결과 목록 깜빡임 수정. skipDebouncedSearchRef + selectPlace에서 results/error 비움. 
unSearch는 useMapStore.getState().center + useCallback([], [])로 center deps 재실행 방지.
- **stationsAnchor** (mapStore): 도착지 주변 충전소 fetch 원점. AppShell origin = stationsAnchor ?? coords ?? DAEGU.
- **PlaceSummaryBar**: preview(status===preview)에만 「주변」 chip (즐겨찾기 보조·도착지 주변 조회). 길찾기 시작 후 숨김. 카드 max-w 280, 길찾기는 shrink-0. queryNearbyStations → anchor + 시트 half + 지도 중심.
- **routeStore**: setDestination / clearDestination / startDirections 시 anchor 해제. clearDestination({ keepStationsAnchor }) 옵션 추가.
- **mapStore.selectStation**: preview 닫을 때 clearDestination({ keepStationsAnchor: true }) — 충전소 탭 시 GPS refetch로 상세가 사라지던 버그 수정.
- **RadiusControl** (잠금 예외 승인): 원·1/2/3 카메라 중심 = stationsAnchor → coords → mapCenter. 줌 프리셋·탭 시에만 카메라·fitBounds 금지 유지. docs/important.md §2.3 갱신.

### 결정
- 「주변」= 즐겨찾기 추가용 부산물(즐겨찾기 탭에 검색 대신). AI 충전확률과는 별 CTA(미구현).
- BE stations API 변경 없음 — 같은 lat/lng/radius_km에 도착지 좌표로 재요청.
- 현위치 주변조회와 도착지 조회는 동일 fetch/마커, origin(anchor)만 구분. 새 TSX 불필요.
- ×·길찾기·새 검색은 anchor 해제. 충전소 선택만 anchor 유지.

### 다음
- 실기기: 검색→주변→목록/마커→상세·별 / 반경 2·3km 도착지 유지 / × 후 GPS 복귀 확인.
- (선택) 길찾기 시작 시 검색어 clear — 웹 polish, 필수 아님.

## 2026-08-04 — stations 목록에 chargers[] 중첩 (chgerId·status)

### 한 일
- BE StationItem.chargers: info⋈status 충전기 행을 JSON_ARRAYAGG로 중첩. 필드: chgerId, chgerType, output, chargerStatus, lastUpdated.
- list_stations_near / list_stations_viewport 동일. 집계(availableCount 등) 규칙 유지.
- FE 	ypes/station.ts에 Charger / chargers? 타입만 추가 (UI 미표시).
- stations_api.md (api/web) 문서 반영.

### 결정
- 목록에 미리 실어 두고 가용대수→버튼 UI는 후속. 대구·limit 규모면 페이로드 OK. 커지면 상세 전용 API로 분리 검토.
- 최상위 아이템은 계속 stat_id 집계.

### 다음
- 가용대수 버튼 → chargers[]로 개별 status 표시.
- (선택) 클릭 시 실시간 status 재조회 vs 목록 스냅샷 사용 정책.

## 2026-08-04 — chargers[]에 info 전 컬럼 확장

### 한 일
- ChargerItem: ev_charger_info 전 컬럼(+ infoUpdatedAt) + status(chargerStatus, lastUpdated).
- JSON_ARRAYAGG JSON_OBJECT 확장. stat_id는 상위 stationId와 중복이라 중첩 생략.
- FE Charger 타입·stations_api.md 동기화.

### 결정
- 패널용으로 쓸 수 있는 대별 필드는 목록에 미리 실어둠. UI는 후속.

### 다음
- 가용대수 버튼 → 충전기 패널 (FE).

## 2026-08-04 — 추천 API env / Settings 연동

### 한 일
- pi/.env.example · .env: RECOMMEND_API_BASE_URL / TIMEOUT / KEY (키 실값 없음).
- config.py Settings에 동일 필드 추가. README env 이름만 표기.

### 결정
- 추천은 외부 HTTP. 키는 담당자 배포·git 금지.

### 다음
- recommendations 라우터 프록시 + CamelModel 스키마 (가이드 §4).

## 2026-08-04 — FE AI 추천 목록·마커 (길찾기 전)

### 한 일
- recommendStore + fetchRecommendations 연동.
- PlaceSummaryBar「AI 추천」: 도착지 기준 점수 조회 (주변 stations 조회 없음).
- RecommendStationPanel 점수순 목록 → 선택 후 길찾기.
- RecommendMarkers: 추천 결과만 지도 마커. AI 모드 중 StationMarkers 숨김.

### 결정
- 빨간 도착 마커는 추천 중심. 길찾기 출발=현위치, 도착=고른 추천 충전소.

### 다음
- 실기기: 검색→AI 추천→목록/마커→길찾기 확인.

## 2026-08-04 — AI 추천 연동 현황 정리 (aimodel.md)

### 한 일
- 워크스페이스 루트 imodel.md 작성 (git 추적 제외, .gitignore 등록).
- BE 프록시 + FE AI 목록/마커/반경 숨김까지 현 상태·다음(stations statId 매칭) 문서화.
- teamdeveloper에 본 블록 추가.

### 결정
- 모델 응답에 포트·가용대수 없음 → FE에서 도착지 stations 병렬 조회 후 statId 매칭 (BE 추가 불필요).
- aimodel.md는 부모 워크스페이스 전용 — web/api 리포에 넣지 않음.

### 다음
- FE: AI 선택 시 포트·대수 보조 패널 (stations 매칭).

---

## 2026-08-05 — DB_BACKEND local|supabase env

### 한 일
- `DB_BACKEND=local|supabase` 전환. local=`DB_*`(mysql), supabase=`SUPABASE_DB_URL`(Postgres URI → psycopg2).
- `is_db_configured`·`.env.example`·README·rules 키 이름 반영. `psycopg2-binary` 추가.

### 결정
- FE anon 키는 이번 범위 밖(BE SQLAlchemy 직결). MySQL 전용 SQL은 supabase 전환 후 별도 정리.

### 다음
- `.env`에 `SUPABASE_DB_URL` 채운 뒤 `DB_BACKEND=supabase`로 접속 확인. 스키마/마이그레이션은 후속.

---

## 2026-08-05 — 로컬 MariaDB → Supabase 데이터 이전

### 한 일
- Docker Desktop 기동. pgloader는 SSL 검증 이슈로 포기.
- 호스트 Python(`scripts/migrate_local_to_supabase.py`)으로 9테이블 이전 완료
  (ev_charger_info 25399, status 16230, users 6, cars 2, car_models 35 등).
- Direct `db.*`는 IPv6-only → Session pooler `ap-northeast-1` 사용. config가 direct URI를 pooler로 재작성.

### 다음
- `DB_BACKEND=supabase`로 앱 기동 후 stations 등 동작 확인. MySQL 전용 SQL 호환은 별도.

---

## 2026-08-05 — stations SQL DB_BACKEND 분기

### 한 일
- `stations/service.py`: `DB_BACKEND=local` → MySQL(`IFNULL`/`GROUP_CONCAT`/`JSON_ARRAYAGG`), `supabase` → Postgres(`COALESCE`/`STRING_AGG`/`JSONB_AGG`).

### 다음
- supabase로 stations 목록·viewport 재확인.

---

## 2026-08-05 — Supabase Edge status sync (BE sync 유지)

### 한 일
- `supabase/functions/fetch-and-upsert`: sync.py와 동일 흐름(getChargerStatus 파싱·정규화·info FK 필터·chunk upsert).
- FastAPI `EV_STATUS_SYNC`는 그대로. Edge 켤 때 BE sync OFF 권장 (README).

### 다음
- secrets/`DATA_GO_KR_KEY` 설정 후 deploy·cron. 수동 invoke로 written 건수 확인.

---

## 2026-08-05 — getApiBase Vercel+LAN · 소셜 자사 JWT

### 한 일
- FE `getApiBase`: 사설 IPv4(LAN)일 때만 `http://{host}:8000`. Vercel/커스텀 도메인은 `NEXT_PUBLIC_API_BASE_URL`(Render 등).
- `npm run dev:lan` 스크립트 복구.
- 소셜: `startOAuthRedirect` 실제 이동. BE 콜백이 `#accessToken=` fragment로 FE에 전달 → `consumeOAuthAccessTokenFromUrl` → localStorage Bearer → `/me`.
- 문서: `06_auth_me`, `auth_api`, `.env.example` (Vercel/FRONTEND_ORIGIN 주석).

### 결정
- 소셜/세션은 **우리 FastAPI(Authlib)+JWT+Bearer**. Supabase Auth 미사용 — DB만 Supabase(편의), 이후 AWS 등 교체 가능.
- 쿠키는 보조; 크로스 오리진(Vercel↔Render)은 fragment 토큰이 본체.

### 다음
- Vercel: `NEXT_PUBLIC_API_BASE_URL`=Render URL, TMAP 도메인. Render: `CORS_ORIGINS`/`FRONTEND_ORIGIN`=Vercel, OAuth redirect URI·시크릿.
- 소셜 콘솔 redirect를 Render HTTPS로 등록 후 스모크.

## 2026-08-05 — 주변 탐색(map) 모드: 칩 진입 + pan 연속 조회

### 한 일
- 같은 칩 스위칭: 「주변 탐색하기」↔「현위치로 돌아가기」(선명 칩). 조회 원점 ~500m 이상일 때 진입 칩.
- 탭 시 stationsAnchor source=map → 반경 원 없음, pan idle 450ms + 250m 이상이면 카메라 중심 재조회.
- OFF: 칩「현위치로 돌아가기」/ ◎ 현위치 / 카메라가 GPS 300m 이내 자동 해제.
- 카메라 sync: MapView 잠금 유지. useSyncMapCenterFromCamera(pointerup·dragend → getCenter).
- policy: web/src/lib/map/mapSearchPolicy.ts (거리·debounce·ALLOW 플래그).

### 결정
- 기본 강점(현위치·도착지) 유지. 카메라 추종 조회는 명시 진입 후에만.
- 매 프레임 조회 금지 — idle debounce + 거리 throttle.
- map 모드에서는 반경 원을 그리지 않음 (도착지 pin·here는 기존).

### 다음
- 체감 민감도(500/300/250/450ms) 조정. AI 중 진입은 policy false 유지.

## 2026-08-06 — Render: requirements.txt UTF-8 · Python 3.11

### 한 일
- \pi/requirements.txt\ UTF-16(널 바이트) → UTF-8 재저장. Render \pip install\ Invalid requirement 해소.
- \pi/.python-version\ = .11.11\ (Render 기본 3.14 회피).

### 결정
- Linux/Render용 텍스트는 UTF-8. Windows에서 requirements 저장 시 UTF-16 금지.

### 다음
- api 커밋·푸시 후 Render 재배포. Env: \CORS_ORIGINS\/\FRONTEND_ORIGIN\=Vercel URL, \APP_ENV=production\.

## 2026-08-10 — 소셜 로그인 FE: oauthError + 버튼 로딩

### 한 일
- `web/src/lib/auth/oauth.ts`: `formatOAuthError` 추가 (BE `/login?oauthError=` 문구 매핑).
- `web/src/app/login/page.tsx`: oauthError useEffect, 소셜 버튼 disabled/onStart/이동 중 라벨, 로컬 `formatLoginError` 분리.
- `web/src/components/auth/LoginBottomSheet.tsx`: 문구 「로그인하기」 + 일반 버튼 스타일 (`/login` 진입, 카카오 직행 아님).

### 결정
- 소셜 시작 URL·토큰 소비는 기존 `startOAuthRedirect` / `handlePostLoginLanding` 유지. 전용 콜백 페이지 없음.
- 시트는 로그인 페이지로 보내고, 소셜 선택은 로그인 화면에서.

### 다음
- 제공자 콘솔 redirect + BE env 스모크 (카카오/구글/네이버 실로그인).
- 실패 시 `/login?oauthError=` UI 확인.

## 2026-08-11 — 네이버 소셜 닉네임: 네이버+번호

### 한 일
- pi/app/domains/auth/service.py: 네이버 가입 시 UI nickname을 네이버+4자리 랜덤(예: 네이버4821)으로 생성. 식별값(
aver_{id}) 노출 제거.
- 기존 
aver_… 닉네임 계정은 다음 로그인 시 1회 교체.

### 결정
- TopBar 표시값은 user.nickname이 맞음 (userId/provider_id 아님).
- 네이버 프로필 nickname/name은 쓰지 않음 — 식별형·비공개 스코프 대비.

### 다음
- API 재시작 후 네이버 재로그인으로 TopBar 닉네임 확인.

## 2026-08-11 — 소셜 닉네임 통일: 구글/카카오/네이버+번호

### 한 일
- pi/app/domains/auth/service.py: 구글·카카오·네이버 가입 UI nickname을 구글/카카오/네이버+4자리로 통일. 프로필명·이메일·식별값 미사용.
- 기존 소셜 계정은 다음 로그인 시 새 형식이 아니면 1회 교체.
- 일반(local) 로그인은 가입 시 입력한 nickname 그대로 TopBar 표시 (변경 없음).

### 결정
- TopBar는 항상 user.nickname. 소셜만 자동 생성, 로컬은 사용자 입력값.

### 다음
- API 재시작 후 카카오/구글/네이버·일반 로그인 TopBar 확인.

## 2026-08-11 — 카카오 OAuth: profile_nickname scope 제거

### 한 일
- pi/app/domains/auth/service.py: 카카오 authorize scope에서 profile_nickname 제거.
- 원인: 콘솔 동의항목이 사용 안 함인데 scope를 요청해 인가 코드 오류 발생.

### 결정
- 소셜 닉네임은 서버 생성(카카오+번호)이므로 카카오 프로필 동의 불필요. 콘솔은 사용 안 함 유지.

### 다음
- API 재시작 후 카카오 로그인 재시도.

## 2026-08-11 — 카카오 토큰 교환: client_secret_post

### 한 일
- 로그: kakao/callback 500 — invalid_client: Not exist client_id [null].
- 원인: Authlib 기본 client_secret_basic(헤더) → 카카오가 body client_id를 null로 인식.
- exchange_code_for_token에 token_endpoint_auth_method=client_secret_post 적용. OAuthError→HTTPException.

### 결정
- 소셜 토큰 교환은 form body 인증으로 통일 (카카오/구글/네이버).

### 다음
- API reload 후 카카오 로그인 재시도.


## 2026-08-11 — 사업자 충전요금 테이블(CSV·DDL) 초안

### 한 일
- 원본 통합 요금 CSV + DB 미매칭 보충분을 usi_id/member_type 스키마로 적재용 CSV 생성.
- 파일: docs/data/ev_operator_tariffs_import.csv (222행, 사업자 111×회원/비회원), docs/data/ev_operator_tariffs.sql (Postgres DDL).
- 빌드 스크립트: docs/data/build_ev_operator_tariffs_import.py.
- 애매 사업자(EZ/YC 등)는 통합 CSV 밴드 median으로 default 보강.

### 결정
- PK/조인: (busi_id, member_type). 충전소 조인은 usi_id만. operator_nm은 표시용.
- member_type: member | 
on_member. 단가 컬럼: 
ate_slow_* / 
ate_mid_* / 
ate_fast_* / 
ate_ultra_* + default_rate.
- ev_charger_info에 DB FK는 걸지 않음(usi_id 비유니크).

### 다음
- Supabase/DBeaver에서 DDL 실행 후 import CSV 적재. BE ORM·API 노출은 별도 승인 후.

## 2026-08-11 — AI 추천 길찾기 → StationDetailCard 통일

### 한 일
- AI 목록에서 길찾기 시 `ensureStationLoaded`로 `statId` → `GET /stations` hydrate 후 `upsertStations`.
- `startDirections` → 기존 `StationDetailCard` Directions(세부·ETA). AI 전용 내비 UI 없음.
- `PlaceSummaryBar`: `recommendActive`면 숨김(목록과 CTA 중복 방지). 닫기 시 요약바 복귀.
- `mapStore`: `upsertStations` + `setStations` 시 선택 중 station 유지(AppShell 교체와 경합 방지).
- 가이드: `mapguides.md` §2.6 · 시나리오 J. `mapguide.md`는 리다이렉트만.

### 결정
- 조회(추천)만 AI 차별. 길찾기·세부는 일반 지도와 동일 UI.
- BE 변경 없음(근처 stations API 재사용). AI 플로우에서 `selectStation` 금지.

### 다음
- 실기기: 검색→AI→목록→길찾기→DetailCard Directions / 닫기→요약바 복귀 확인.

## 2026-08-11 — AI 목록 탭 → DetailCard 미리보기

### 한 일
- AI 행/추천 마커 탭: `ensureStationLoaded` + `focusStationOnMap`(destination 유지) → 기존 DetailCard 기본정보.
- DetailCard 길찾기: `recommendActive`면 비활성(패널 CTA만 길찾기).
- `mapStore.focusStationOnMap` 추가 (`selectStation`과 분리).

### 결정
- 마커 탭과 동일 수준의 정보만. 새 페이지·BE 없음.

### 다음
- 실기기: 목록/마커 탭→Detail · 길찾기 비활성 · 패널 CTA→Directions 확인.

## 2026-08-11 — AI 목록 Detail 미리보기 시 패널 접기

### 한 일
- Detail이 열리면 RecommendStationPanel을 한 줄(이름·목록·닫기)+길찾기 CTA로 접음.
- 「목록」→ Detail 닫고 목록 재펼침(모바일 공간).

### 결정
- 목록+Detail 동시 풀사이즈 금지(모바일 가림).

### 다음
- 실기기 좁은 화면에서 접힘/목록/길찾기 확인.

## 2026-08-11 — 주변 카테고리 칩 UI 스텁

### 한 일
- PlaceCategoryChips: 맛집·카페·편의점·주차장 칩 (탭 토글 UI만, API 없음).
- MapSearchBar 검색바 펼침 시에만 표시 (모바일 아이콘 접힘 = 칩 숨김).

### 결정
- 접힘 상태엔 칩 상시 노출 안 함. BE around 연동은 이후.

### 다음
- BE places around 프록시 + 칩 → 검색/마커 연동.

## 2026-08-11 — places around (TMAP 카테고리) 프록시

### 한 일
- BE GET /api/v1/places/around — TMAP /pois/search/around 프록시.
- client.fetch_tmap_around_places + 공통 _normalize_pois. radius 1~33 클램프.

### 결정
- 응답은 기존 PlaceResult 재사용. FE 칩(맛집/카페/편의점/주차장) 연동은 다음.

### 다음
- FE searchPlacesAround + PlaceCategoryChips 연동.

## 2026-08-11 — FE places around 칩 연동

### 한 일
- searchTmapPlacesAround → BE /places/around.
- MapSearchBar 
unCategorySearch: center + radiusKm, 성공 무메시지, 실패 console.error.
- 칩 토글 off clear · query clear 레이스(skipDebouncedSearchRef) 수정.

### 결정
- 반경=지도 radiusKm. 마커는 아직 없음(리스트만).

### 다음
- 실기기 칩→목록→선택 destination 확인. 카테고리 마커(선택).

## 2026-08-11 — 카테고리 POI 전용 마커

### 한 일
- 칩별 SVG 핀(맛집/카페/편의점/주차장) + PlaceCategoryMarkers.
- placeCategoryStore로 리스트·마커 공유. MapView 조합만(SDK 락 미변경).

### 결정
- 리스트 유지 + 마커 병행. 티맵 내장 카테고리 아이콘 없음 → FE SVG.

### 다음
- 실기기: 칩→핀·목록→탭 destination 확인.

---

## 2026-08-11 — places/around 중심·건수

### 한 일
- 카테고리 around 조회 중심: map \center\만 쓰던 것을 충전소와 동일하게 \stationsAnchor → GPS → center\로 맞춤 (\MapSearchBar\).
- 건수: BE \count\ 쿼리(1~200, 기본 50). FE \placeAroundLimitForRadiusKm\ — 1km→50 / 2km→100 / 3km→150.

### 결정
- stations limit(3km→200)과 places(3km→150)는 분리 유지.

### 다음
- 칩·반경 변경 시 마커 수·원점 체감 확인.

---

## 2026-08-11 — 모바일 카테고리 칩: 결과 리스트 닫기

### 한 일
- compact에서 카테고리 around 실행 시 \setOpen(false)\ — 검색 결과 패널 미표시(마커·store는 유지). 데스크톱은 기존처럼 리스트 오픈.

### 다음
- 모바일에서 칩 탭 → 리스트 없이 지도 마커만 확인.

---

## 2026-08-11 — 모바일 카테고리 마커 탭

### 한 일
- PlaceCategoryMarkers: StationMarkers와 동일하게 map DOM capture 탭 hit-test (TMAP Marker click 미신뢰).
- 충전소·카테고리 POI가 겹치면 더 가까운 쪽 선택(동거리면 POI). earestLatLngItem\ 공유.

### 다음
- 모바일에서 칩 → 마커 탭 → 도착지/요약바 확인.

---

## 2026-08-11 — PlaceSummaryBar AI 숨김 (POI)

### 한 일
- \destination.stationId\ 없을 때(카테고리·키워드 POI) AI 추천 버튼 숨김. 길찾기만 노출. 충전소 도착지는 유지.

### 결정
- 비활성 대신 숨김 (혼동·죽은 컨트롤 방지).

### 다음
- 카테고리/검색 장소 선택 → AI 없이 길찾기만 확인.

---

## 2026-08-11 — 자유주행 시 카테고리 자동 재검색

### 한 일
- 칩 활성 + 자유주행(testMode)에서 coords가 마지막 around 원점 대비 ≥150m 이동하면 silent 재검색.
- stationsAnchor(도착지) 있으면 스킵.

### 다음
- 칩 켠 뒤 자유주행 탭 → 마커가 새 점 주변으로 갱신되는지 확인.

---

## 2026-08-12 — 검색 input 기본 clear 숨김

### 한 일
- `type="search"` WebKit/Blink 기본 ✕(`::-webkit-search-cancel-button`)를 globals.css에서 숨김.
- MapSearchBar·AddressSearchModal의 커스텀 지우기/닫기 버튼만 유지.

### 결정
- 커스텀 clear 유지(결과·카테고리까지 clearQuery로 정리). native는 UI 중복·브라우저별 차이로 제거.

### 다음
- 모바일/데스크톱에서 검색어 입력 시 ✕가 하나만 보이는지 확인.

---

## 2026-08-12 — compact UI: md: 폭 충돌 제거 (가로 폰)

### 한 일
- 앱/웹 크롬을 Tailwind `md:`가 아니라 `useCompactLayout`(터치1차 또는 ≤767)만으로 게이트.
- AppShell: 사이드 패널·목록 토글·MobileStationSheet 마운트를 `isCompact`로 분리. `data-layout` 표기.
- MobileBottomNav / MobileStationSheet: `md:hidden` 제거.
- MapView FAB·상세 카드 위치: `md:bottom-4` 대신 compact면 시트 offset 유지.

### 결정
- 가로 금지 없음. 폰 가로는 터치1차 → compact 유지(앱 UI).
- 동일 크롬을 `md:`로 다시 가리지 않음(폭≥768에서 네비/시트 사라지던 버그).

### 다음
- 실기기 폰 가로: 하단 네비·시트·FAB가 앱 UI로 남는지 확인. 태블릿 웹 분기(폭 임계)는 추후.

---

## 2026-08-12 — compact: 폭 ≥900이면 웹 UI

### 한 일
- `useCompactLayout`: `min-width: 900px` → 항상 desktop(웹). 그다음 터치1차 → compact, 그외 ≤767 → compact.
- Fold8 펼침(~816)은 900 미만이라 앱 UI 유지. iPad 등 넓은 터치는 웹.

### 결정
- 넓은 화면이면 앱 UI(하단 네비·시트) 의미 적음 → 폭 우선. 가로 금지는 계속 없음.

### 다음
- 태블릿 가로·폰 가로·Fold 펼침에서 앱/웹 전환 확인.


## 2026-08-12 — places PlaceResult 업종·주차 필드

### 한 일
- PlaceResult에 middleBizName / lowerBizName / parkFlag(optional) 추가.
- client._normalize_pois: TMAP 원본 매핑 + _clean_biz_name(기타→null) / _parse_park_flag.
- services._to_place_results에 동일 필드 전달 (optional이라 필터에서 제외하지 않음).

### 결정
- 업종 표시 우선순위: lower → middle. parkFlag는 true일 때만 UI 표시(false/null 침묵).
- search·around 공통 normalize.

### 다음
- FE TmapPlaceResult 타입 반영됨. PlaceSummaryBar·destination에 업종/주차 뱃지 표시.

## 2026-08-12 — places 업종·주차 FE 요약바 연동

### 한 일
- RouteDestination / TmapPlaceResult에 middleBizName·lowerBizName·parkFlag.
- PlaceCategoryMarkers·MapSearchBar 선택 시 destination에 전달.
- PlaceSummaryBar: lower→middle 업종 라벨, parkFlag true만 «주차 가능».

### 결정
- 없으면 행 생략. 긴 상호 line-clamp는 미적용(추후 선택).

### 다음
- 실기기에서 카테고리/검색 선택 시 업종·주차 표시 확인.

## 2026-08-12 — 도착지「이 주변 충전소」지도 칩

### 한 일
- \DestinationNearbyChip\: 검색 도착 핀(preview)일 때 지도 상단 중앙에 「이 주변 충전소」칩. PlaceSummaryBar「주변」과 동일 로직(\stationsAnchor\ source=destination).
- AppShell: 「이 주변 충전소」+「주변 탐색하기」세로 스택(gap-2). 카드「주변」버튼은 유지.
- 공통 헬퍼 \lib/map/queryNearbyStations.ts\ (\queryNearbyStationsAt\).
- 현위치 버튼: destination·map 앵커 모두 해제 → GPS 기준 목록/마커 복귀(도착지 카드는 유지, 칩으로 재조회 가능).

### 결정
- 「주변 탐색하기」(map pan)와 「이 주변 충전소」(도착지 고정)는 별 기능·별 라벨. 같은 슬롯에 세로로 쌓음.
- 카드「주변」은 보조 진입으로 유지.

### 다음
- 실기기: 검색 선택 → 상단 칩·카드「주변」→ 목록/마커 → 현위치 → GPS 복귀 → 칩 재탭 확인. 멀리 팬 시 「주변 탐색하기」와 동시 노출 확인.

## 2026-08-12 — 메뉴 UI 껍데기 (즐겨찾기·차량·마이페이지)

### 한 일
- FavoritesPanel: 목록/추가 탭. 목록은 StationList형 빈 상태+행 미리보기. 추가는 전용 검색창 + DB(stat_id·memo) 입력 폼(기능 미연결).
- CarPanel: 기종 콤보(car_models 껍데기) + 「포트 덮어쓰기」버튼(끄면 기종 기본 포트). 기존 임시 포트 테스트 UI 유지.
- MyPagePanel 신규: 회원 정보 수정/삭제 폼, AddressSearchModal 재사용, 주요 메뉴 바로가기, 주변조회·날씨조회 버튼 껍데기.
- IconRail/하단내비 라벨 「설정」→「마이페이지」. AppShell·MobileStationSheet에 패널 연결.

### 결정
- API·저장 로직은 붙이지 않음. NavId는 settings 유지(라벨만 변경).
- 즐겨찾기 검색은 MapSearchBar와 분리한 전용 입력 껍데기.

### 다음
- favorites/cars/auth 회원수정 API 연동. 기종 콤보에 car_models 목록 fetch.

## 2026-08-12 — 포인트 패널 mockup

### 한 일
- PointsPanel: 현재 잔액(authStore.pointsBalance), 충전/사용 CTA 껍데기, point_transactions형 사용 내역 mock 리스트.
- AppShell·MobileStationSheet points 탭에 연결 (UnimplementedHint 제거).

### 결정
- 내역은 하드코딩 mock. 충전·사용 버튼은 no-op.

### 다음
- point_wallets / point_transactions / payments API 연동.

## 2026-08-12 — 카테고리 POI 업종 칩 라벨 폴백

### 한 일
- around API는 middle/lowerBizName 미제공. PlaceCategoryMarkers pickPlace에서 둘 다 없으면 PLACE_CATEGORY_CHIPS 라벨(음식점·카페 등)을 middleBizName으로 넣음.
- placeCategoryLabel 헬퍼 추가.

### 결정
- 추가 TMAP 호출 없음. 키워드 검색(통합) 값은 그대로 우선.

### 다음
- 실기기: 카테고리 마커 탭 시 PlaceSummaryBar에 칩 라벨 표시 확인.

## 2026-08-12 — 충전소 마커 숫자 콜아웃(팁 앵커)

### 한 일
- \lib/tmap/stationCalloutMarker.ts\: 원형 canvas 마커 → 둥근 사각 + 아래 팁 SVG 콜아웃. 가용 숫자 강조, \/총\ 유지. 앵커=팁 끝.
- \StationMarkers\만 교체. 카테고리 핀·현위치·도착·RecommendMarkers 원형 유지.

### 결정
- 총대수 표기 유지(피드백은 가독성). 겹침은 완전 해소가 아니라 위치·숫자 가시성 완화 목적.
- 되돌리기 쉬운 시안 — 아이콘 생성만 분리.

### 다음
- 실기기에서 \8/12\ 가독·선택 스트로크·밀집 구간 체감 확인. 마음에 안 들면 원형으로 롤백.

## 2026-08-12 — 충전소 마커 겹침 cascade 시안 (아래 밀기)

### 한 일
- \lib/map/stationMarkerCascade.ts\: 화면상 근접 충전소를 그룹으로 묶어 슬롯마다 남쪽(아래)으로 표시 좌표만 오프셋. 탭 hit는 실제 lat/lng 유지.
- \StationMarkers\: 줌·선택 변경 시 cascade 재적용. 선택 충전소는 그룹 내 slot 0(원래 자리). zIndex 미의존.

### 결정
- SDK/MapView/RadiusControl 미변경. 테스트 시안 — 체감 안 좋으면 cascade만 제거.

### 다음
- 실기기 밀집 구간·줌인아웃·선택 시 자리 복귀 확인.

## 2026-08-12 — 겹침 시안: 위치 cascade → 팁 상하 플립

### 한 일
- 의도 정정: 좌표를 아래로 밀지 않고, 콜아웃 화살(팁)을 위/아래로 뒤집어 몸통을 양쪽으로 나눔.
- \stationCalloutMarker\: tipDirection down|up. 겹친 페어는 하나 위·하나 아래. 좌표는 실제 lat/lng 유지.

### 결정
- zIndex/위치 오프셋 시안은 의도 아님. 2개 겹침에 유효, 3개+는 같은 방향끼리 다시 겹칠 수 있음.

### 다음
- 실기기에서 페어 겹침 구간 확인.

## 2026-08-12 — 겹침: 아래층(낮은 z)만 팁 플립

### 한 일
- \calloutStackLayout\: 겹침 그룹에서 위층(선택 우선)=tip↓ + z 70/80, 가려진 쪽=tip↑ + z 50↓.
- StationMarkers에서 setIcon과 함께 setZIndex 적용.

### 결정
- 클릭/가독이 막히는 아래층이 뒤집히도록. 좌표는 실제 lat/lng 유지.

### 다음
- 실기기 페어 겹침에서 아래 마커 탭·숫자 확인.

## 2026-08-12 — 겹침: 팁 플립 폐기 → 표시좌표 cascade

### 한 일
- 팁 상하 뒤집기 제거(콜아웃은 항상 tip↓). 목표를 「안 겹침」으로 정정.
- \cascadeMarkerLayout\: 근접 그룹에서 선택/위층은 제자리, 나머지는 화면 ~40px만큼 남쪽으로 표시만 이동. 탭 hit는 실제 lat/lng.

### 결정
- 뒤집으면 몸통이 반대로 붙으며 오히려 겹쳐 보임. declutter는 위치 오프셋.

### 다음
- 실기기 밀집 구간에서 세로로 벌어지는지·선택 시 제자리 복귀 확인.

## 2026-08-12 — cascade: 선택 시 자리 고정

### 한 일
- cascade 슬롯은 stationId 고정 정렬. 선택은 icon/zIndex만(자리 재배치 없음).
- 위치 sync는 list·줌만. 클릭으로 마커가 우르르 움직이지 않게.

### 결정
- 목표=그려질 때 안 겹침. 클릭 이동은 부작용이라 제거.

### 다음
- 실기기: 최초 표시에서 세로 분리·탭 시 자리 유지 확인.

## 2026-08-12 — 충전 결제·포인트 정리 문서

### 한 일
- 워크스페이스 루트에 `payment.md` 신설 (기존 payment 전용 문서 없음).
- 컨셉(포인트 대행·회원가 기준 데모), 기존 지갑 3테이블, 요금표, 예정 `usage_orders`/`partners`, kWh UX, 실연동 방향을 표로 정리.

### 결정
- 요금표 참고와 포인트 대행 레이어 분리. 가짜 제휴로 자격 흉내 내지 않음.
- 토이 대행 단가 = 요금표 회원가 × 사용자 kWh(칩+수동). 실세션·상용 정산 제외.

### 다음
- 요금 표시·지갑 API·usage_orders 는 각각 BE 승인 후 구현.

## 2026-08-12 — payment.md 대표가·매칭·가용 기 보강

### 한 일
- `payment.md`에 단가 매칭(busiId+output), DetailCard 비회원 대표가, 회사 vs 충전소 대표가, 가용 chargers(status=2)·FE만, 포트별 가격 비표시를 반영.

### 결정
- 충전소 대표가 = 가용 max output 밴드 비회원가. 회사 목록 = default_rate 또는 min~max (완속/최저가 단독 ❌).

### 다음
- 요금 API·DetailCard 표시는 BE 승인 후.

## 2026-08-12 — payment.md 기존 3테이블 검토 + 신규 DDL 부록

### 한 일
- `payment.md` §2.0: `point_wallets` / `point_transactions` / `payments`는 usage_orders·요금 대행을 위해 **ALTER 불필요**로 확정 (`ref_type=usage_order` 자리 기존 확보).
- §4.1 구현 규칙 반영: confirm 3중 원자성·잔액부족=롤백(failed 없음)·kWh CHECK·points_spent 단일 함수·idempotency=confirm 전용.
- §10 DDL 부록: `ev_operator_tariffs`(CSV 기준), `usage_orders`, `partners`(1차 주석·미적용).

### 결정
- 기존 지갑 3테이블 스키마 수정 없음. 제휴 컬럼/affiliations 추가 없음. `ev_charger_status` 데모 변조 금지.
- 신규 생성 순서: 요금표 → (지갑 API) → usage_orders. partners는 제휴 확정 전 생략.

### 다음
- DB 승인 후 §10 DDL 적용 + CSV import. usage_orders API는 BE 승인 후.

## 2026-08-12 — payment DDL MariaDB + PostgreSQL 이중본

### 한 일
- `docs/data/payment_ddl_postgresql.sql`, `docs/data/payment_ddl_mariadb.sql` 신설 (요금표+usage_orders+partners주석).
- `payment.md` §10에 두 방언 전문·차이표 반영. 기존 지갑 3테이블 ALTER 없음 유지.

### 결정
- Supabase(Postgres)가 주 타깃이어도 MariaDB 사본을 문서/파일로 유지 (이관·로컬 대비).

### 다음
- 실제 적용 DB 선택 후 해당 파일만 실행 + CSV import.

## 2026-08-12 — 요금 폴백 센티널 __AVG__ CSV 반영

### 한 일
- `ev_operator_tariffs_import.csv`에 `busi_id=__AVG__` member/non_member 2행 추가 (밴드 median, 224행).
- `build_ev_operator_tariffs_import.py`에 센티널 자동 주입. `payment.md` §3.1.1~3.1.2 조회·관리·DDL 주의 추가.
- DDL 주석: FK 금지, `__DEFAULT__`(11자) 대신 `__AVG__`(7자).

### 결정
- 매칭 실패·busi_id null → `__AVG__` 폴백. UI는 추정·평균 기본가. 요금 정본은 CSV.

### 다음
- DB import 시 센티널 포함 재적재. 조회 로직에 폴백 순서 구현(BE 승인 후).

## 2026-08-12 — cascade 파라미터 완화 (원 밖 과도 밀림)

### 한 일
- \stationMarkerCascade.ts\: COLLIDE_PX 96→56, MIN_COLLIDE_M 90→45, STEP_PX 44→28, MAX_SLOT 8→3.
- 표시좌표만 남쪽 밀기 유지. 탭 hit는 실제 lat/lng 그대로.

### 결정
- 줌15 기준 충돌·슬롯 밀림이 반경 원 밖으로 과하게 나가 체감이 나쁨 → 내일 실기기 재테스트용 완화.

### 다음
- 밀집 구간에서 겹침·원 밖 이탈 체감 확인. 더 세면 추가 완화 또는 cascade 제거.

## 2026-08-13 — 회원 메뉴 UI 게이트·카피 정리

### 한 일
- 즐겨찾기·내 차량·포인트 패널: 비로그인 시 상단 배너 + 메뉴 열람 유지. 등록/충전 버튼은 비활성.
- 목록·상세 ★: 비로그인이면 별 미채움, 「즐겨찾기 기능은 로그인 시 제공됩니다」 시트.
- 포인트 mockup에서 balance·테이블명 등 DB 용어 제거. 마이페이지 회원번호 필드 삭제.
- 즐겨찾기·차량 폼의 DB 컬럼 안내 문구 제거.

### 결정
- 패널 진입은 막지 않고 위 안내만. 저장 순간에 창을 띄우지 않음(버튼 비활성).
- 지도/충전소 ★만 탭 시 로그인 시트.

### 다음
- favorites/cars API 연동. 로그인 후 배너 숨김·★ 토글 서버 반영 확인.

## 2026-08-13 — AI 추천 후 일반 목록 메뉴 접기

### 한 일
- AppShell: recommendActive가 되면 데스크톱 목록 패널 닫기, 모바일 시트 peek, nav는 map.
- AI 추천 목록과 StationList가 동시에 보이지 않게.

### 결정
- 추천 시작(패널 등장) 시점에 접음. 추천 종료 후 자동 재펼침은 없음.

### 다음
- 실기기에서 AI 추천 탭 → 일반 목록이 접히고 추천 목록만 남는지 확인.

## 2026-08-13 — 즐겨찾기 가용대수 + 시트 모달 포탈

### 한 일
- GET /favorites/list에 availableCount 추가. ev_charger_status JOIN, stations와 동일(관측 없으면 null, 있으면 charger_status=2 대수). 반경과 무관.
- 즐겨찾기 목록 행에 그 수를 표시.
- LoginBottomSheet·AddressSearchModal을 document.body 포탈. 모바일 시트(transform) 안에서 열어도 회색 오버레이가 시트에 갇히지 않음.

### 결정
- 찜 가용은 mapStore 반경 합치기가 아니라 list API 필드. 대구 서비스 범위의 충전소면 카메라 밖이어도 숫자.
- 모달 UI는 유지하고 마운트만 body. TMAP 잠금 파일 미수정.

### 다음
- 로그인 후 즐겨찾기 탭에서 반경 밖 찜도 가용 숫자가 보이는지 확인.
- 모바일 시트에서 ★(비로그인)·마이페이지 주소 검색 시 닫기/로그인이 화면 안에 보이는지 확인.
- 즐겨찾기 추가 탭 검색 연동.

## 2026-08-13 — 즐겨찾기 ★ 등록 연동 (현황)

### 한 일
- 목록·상세 ★ → 로그인 게이트 → POST /api/v1/favorites/toggle → favoriteStore hydrate.
- 즐겨찾기 목록 탭은 저장된 충전소 표시(availableCount 포함).
- 「추가」탭 UI(검색창·선택·메모·제출)는 유지. 검색·제출은 아직 미연결.

### 결정
- 지도에서 ★로 찜하는 1차 등록은 완료로 본다.
- 지도 장소검색(MapSearchBar / TMAP POI)과 즐겨찾기 추가 탭 검색은 별개. 찜은 stationId가 필요해서 POI로 대체하지 않음.
- 반경 목록(mapStore.stations) 클라이언트 필터만으로는 추가 탭 검색으로 쓰지 않음.

### 다음
- 즐겨찾기 추가 탭: 충전소 이름/주소 검색 → 선택 → 메모 → toggleFavorite.
- 검색 API는 GET /api/v1/stations/search (q 2자+, limit, stat_id 집계). 기존 GET /stations(lat/lng/radius)는 유지. BE 작업 전 승인 필요.
- MapSearchBar·TMAP 잠금 파일(loadSdk / MapView bootstrap / RadiusControl) 수정하지 않음.

## 2026-08-13 — 충전소 키워드 검색 API

### 한 일
- GET /api/v1/stations/search 추가. q(2자+)·limit(기본 20/최대 30). stat_nm·addr·addr_detail contains, stat_id 집계.
- 응답 요약만: stationId, name, address, lat, lng, availableCount. chargers[] 없음.
- 기존 GET /stations(lat/lng/radius) 계약 유지. FE 미연결(추가 탭은 프론트에서 붙임).
- stations_api.md (api/docs · web/docs)에 엔드포인트 문서 추가.

### 결정
- 반경 목록에 q를 섞지 않고 /search 분리. 전체 dump 금지.
- 지도 장소검색(TMAP places)과 혼용하지 않음. 찜은 stationId.

### 다음
- FE 즐겨찾기 추가 탭: search → 선택 → 메모 → toggleFavorite.
- OpenAPI /docs에서 /stations/search 확인. q=시청 등 로컬 조회.

## 2026-08-13 — 즐겨찾기 추가 탭 검색 연결 + draft 유지

### 한 일
- FavoritesAddShell: searchStations 디바운스 → 선택 → memo → toggleFavorite. 성공 시 목록 탭.
- 비로그인 추가 버튼 라벨「로그인 후 추가」+ 안내. 미선택 시「검색에서 충전소를 선택하세요」.
- addDraft·addTab을 favoriteStore에 둠. 목록/추가 탭·다른 메뉴를 다녀와도 추가 성공 전까지 유지.
- 검색「초기화」버튼: query·결과·선택 비움(메모는 유지). 추가 성공·로그아웃 시 draft 전체 비움.

### 결정
- 추가 성공 전 draft 유지. 지도 검색(MapSearchBar)과 분리. TMAP 잠금 파일 미수정.

### 다음
- 로그인 후 추가 탭에서 검색→선택→추가→목록·★ 확인. 탭/메뉴 이동 후 draft 유지·초기화 확인.

## 2026-08-13 — 지도 장소검색 대구 우선(제거 없음)

### 한 일
- searchTmapPlaces: 지도 center가 있으면 lat/lng를 BE에 전달. radius는 안 보냄(타 지역 미절단).
- 응답 10개를 재정렬: 주소·이름에 「대구」가 있으면 위, 없으면 아래. 그룹 안 TMAP 순서 유지.

### 결정
- 대구만 남기는 필터 아님. 개수 10 유지. MapView/loadSdk/RadiusControl 미수정.

### 다음
- 「시청」검색 시 대구 결과가 위에 오는지, 「강남」은 서울이 그대로 나오는지 확인.

## 2026-08-13 — 내 차량 API 연동 (FE)

### 한 일
- CarPanel: GET /models 콤보, POST /createCar, 목록·대표·삭제. 로그인 시 폼, 비로그인은 임시 포트만.
- 로그인 hydrate에 cars 포함. logout/clear 시 carStore clear.
- 400 응답은 FastAPI detail 문자열을 alert에 사용.

### 결정
- 차량 내용 수정 PATCH는 1차 제외. 잘못 등록하면 삭제 후 재등록.
- API model → FE carModel 매핑. 커스텀 기종은 포트 필수 UI.

### 다음
- 실기기: 로그인 → 기종 선택 → 저장 → 새로고침 후 목록 유지. 대표/삭제 확인.

## 2026-08-13 — 충전 포트 SVG 시안

### 한 일
- 원본 포트 글리프 3장: `web/public/car/ports/{ccs,chademo,nacs}.svg` (공식 도면 아님, 핀 배치 단순화).
- CarPanel 포트 선택·목록·임시 포트 버튼에 표시. CCS는 한국에서 익숙한 Combo 2 실루엣.
- 차량 가오용 생성 사진 1장 시안: `web/public/car/ev-generic.png` (빈 목록에만, 교체 가능).

### 결정
- 포트는 AI 생성 대신 직접 SVG. 차 사진은 시안 — 외부 에셋으로 바꿔도 경로만 유지.

### 다음
- 내 차량에서 포트 3종 구분 확인. 차 사진 유지/교체 결정.


## 2026-08-14 — 즐겨찾기 POST /toggle 복구

### 한 일
- BE `POST /api/v1/favorites/toggle` 복구. 있으면 해제, 없으면 등록. memo는 신규일 때만.
- 10개 한도는 기존대로 HTTP 200 + `processed: false` (`FAVORITE_LIMIT_REACHED`).
- 명시적 `POST /favorites`, `DELETE /favorites/{stationId}`는 유지. FE 별 버튼·추가 탭은 기존처럼 toggle만 호출.
- 재발 방지: `docs/rules/08_api_http_contract.md`, `.cursor/rules/api-http-contract.mdc`.

### 왜 로컬에선 되는 줄 알았나 (405 원인)
1. **8/11** BE에 원래 `POST /toggle`이 있었다. 그때 ★는 로컬에서 정상.
2. **8/12** 포인트 커밋에서 BE만 add(`POST /favorites`) + remove(`DELETE /{id}`)로 바꿈. FE는 `/toggle`을 그대로 호출.
3. **8/13** FE ★ 연동은 작업 메모「list/toggle 이미 있음」을 따름. `router.py`를 다시 안 봄.
4. `GET /favorites/list`는 그대로 200이라 **목록·로그인은 되는 것처럼** 보였다. ★를 눌러야 POST /toggle 405가 난다.
5. 405인 이유: `/toggle` 전용 POST가 없어 FastAPI가 `DELETE /{station_id}`의 `station_id=toggle`로 경로만 맞추고, 메서드가 POST라 **Method Not Allowed**. 404가 아님.

### 결정
- ★ 클릭은 클라이언트 상태 분기(add vs delete)가 아니라 서버가 DB 보고 토글. 동시 탭은 사용자 행 잠금으로 직렬화.
- HTTP 경로·메서드 변경은 같은 작업에서 FE 호출부를 맞추거나, 맞추기 전에 배포하지 않는다. 작업 메모는 `router.py`보다 우선하지 않는다.

### 다음
- 로컬: 로그인 후 ★ 연속 탭 → 등록/해제 반복, 목록 hydrate. 10개일 때 추가 시도 시 안내 문구.
- Render 배포 후 운영에서도 동일 확인.

## 2026-08-14 — 즐겨찾기 한도 안내 시트 (alert 제거)

### 한 일
- 10곳 초과 시 window.alert 대신 FavoriteNoticeSheet (BodyPortal 하단 시트).
- 문구: 「즐겨찾기는 최대 10곳입니다」 / 「목록에서 하나를 해제한 뒤 다시 추가해 주세요.」
- 처리 실패도 같은 시트. AppShell에 1회 마운트. TMAP 잠금 파일 미수정.

### 결정
- 한도는 등록 차단 + 안내만. 바꿀 항목 선택 UI는 아직 없음.
- 시스템 alert는 모바일에서 도메인 문구·지도 정지가 나서 로그인 시트와 같은 패턴 사용.

### 다음
- 10개 채운 뒤 ★ 추가 시 시트가 지도/모바일 시트 위에 보이는지 확인.

## 2026-08-14 — 즐겨찾기 ★ 낙관적 토글

### 한 일
- ★ 탭 즉시 stationIds 반영. POST /toggle·list hydrate는 뒤에서.
- 10곳 가득이면 켜지 않고 한도 시트. 실패·한도(서버)면 별 되돌림.
- 연속 탭은 pending으로 한 요청만. TMAP 잠금 파일 미수정.

### 결정
- 별 지연은 서버 고장보다 FE가 toggle+list를 기다린 것. 낙관적 UI가 맞음.

### 다음
- 로그인 후 ★ 탭이 즉시 채워지는지, 10개일 때 안 켜지고 시트만 뜨는지 확인.

## 2026-08-14 — Agent 수정 권한: 규모 게이트

### 한 일
- BE 전면 사전승인 → 파일 5개 초과 또는 ~50줄 초과 시 승인·검토로 변경.
- .cursor/rules/backend-permission.mdc, docs/rules/01_agent_permissions.md, docs/important.md §5 + web/api sync, api-files.mdc 정합.

### 결정
- web/·api/ 소규모 수정은 승인 없이 진행 가능. TMAP 잠금은 규모 무관 유지.

### 다음
- (없음 — 규칙만)

## 2026-08-14 — 마이페이지 주소 좌표 PATCH

### 한 일
- PATCH /me에 userLat·userLng 추가 (schema/controller/service).
- FE updateProfile·MyPagePanel 저장 시 주소 검색 좌표 함께 전송.

### 결정
- 가입과 동일하게 프로필 수정에서도 좌표 저장. 비밀번호 PATCH는 여전히 후속.

### 다음
- 마이페이지에서 주소 검색 → 저장 → /me에 좌표 유지되는지 확인.


## 2026-08-14 — 마이페이지 회원 수정·탈퇴·UI

### 한 일
- authStore: provider·주소·좌표 매핑, updateProfile(PATCH /me), withdraw(DELETE /me) + store clear.
- MyPagePanel: /me hydrate, 저장(닉·주소·상세·좌표), 탈퇴 confirm·안내 문구, 성공 시 지도로 패널 닫기.
- UI: 「내 정보 수정」상단 접기/펴기(기본 접힘), 주요 메뉴 일렬(+주변·날씨 비활성 행).
- BE PATCH /me에 userLat·userLng 추가 (가입과 동일).
- login: provider 매핑, 토큰 없으면 assign 금지. CarPanel·GuestAuthBanner 터치 min-h-9.
- 문서: 작업진행상항·auth_api·auth_ux·본 로그. Agent 규모 게이트(파일5+/~50줄+) 반영됨.

### 결정
- 탈퇴는 소프트 삭제 유지(연관 DB 미삭제). 유저 문구는 로그인·이용 불가만.
- 비밀번호 변경은 API 없어 UI 제외. 좌표는 주소 검색 후 저장 시 서버 반영.

### 다음
- 포인트 FE(잔액·내역·PortOne 충전). 마이페이지 주소 검색→저장→좌표 유지 수동 확인.

## 2026-08-14 — 포인트 패널 금액 직접 입력

### 한 일
- PointsPanel: PortOne/ADMIN 자유충전 모두 **입력창 + 프리셋이 창에 값 채움 + 충전 버튼** 흐름으로 변경
- BE 한도(1천~100만 원 / 1~100만 P) 클라이언트 선검증

### 결정
- 프리셋은 즉시 결제하지 않음. 창에 넣은 뒤 충전 버튼만 실행

### 다음
- PortOne env 키 연동 실결제 확인, ADMIN DB role 테스트

## 2026-08-14 — 포인트 충전·ADMIN 자유충전 1차

### 한 일
- PointsPanel: 잔액/내역 연동, 금액 입력+가산 프리셋+초기화, PortOne 충전, ADMIN 자유충전.
- /credit: role=ADMIN만. body nickname으로 대상 유저 지갑 적립(없으면 404). 가입 role은 항상 USER, ADMIN은 DB만.
- authStore·login에 role. 이니시스용 합성 email/phone. POST /charges/fail, 목록에서 pending 숨김.
- TMAP 잠금 파일 미수정. 시크릿 문서 없음.

### 결정
- 자유충전은 환불 아님. user_id 이중 필터 없음. email/전화 컬럼 복구 안 함.
- 실패 내역은 failed로 남김. pending은 쓰레기라 목록 제외.

### 다음
- chger 선택 → 사용량 → usage_orders. PortOne 실결제·웹훅은 수동 확인.

## 2026-08-14 — 소셜 닉네임은 가입 시에만 생성

### 한 일
- upsert_social_user: 기존 계정 재로그인 시 nickname 덮어쓰기 제거. 마이페이지에서 바꾼 닉네임 유지.

### 결정
- 소셜 닉네임(구글1234 등)은 최초 가입에만 부여. 로그인마다 재생성하지 않음.

### 다음
- 구글 재로그인 후 마이페이지 닉네임이 유지되는지 확인.

## 2026-08-14 — 충전 요청 UI 2차 (선택·kWh)

### 한 일
- ChargeRequestPanel: 대기(status=2) 기 목록, 고속 위·출력 높은 순, 4줄+스크롤, kWh 칩 5/10/20/50, 대표차 안내.
- StationDetailCard: 충전 요청→chargeMode, 비로그인 LoginBottomSheet. 충전 모드 하단은 뒤로+결제(길찾기 숨김). TMAP/MapView 미수정.

### 결정
- 상세 카드 하단 2칸을 모드별로 재사용. 카드 통째 리팩터 안 함.
- 완속은 목록에서 빼지 않고 아래로만. 결제 버튼은 기+kWh 유효 시 활성, usage_orders 미연결.

### 다음
- usage_orders request → pre-authorize → complete → pay. BE ev_charger_status 변조는 합의 위반(막히면 최소 수정·승인).

## 2026-08-18 — 마이페이지 사용 안내 QnA

### 한 일
- 마이페이지 기본 화면에 사용 안내 아코디언. 질문 목록은 바로 보임, 답만 펼침.
- 난해한 지도 기능 위주: 주행모드, 마커 숫자, 조회 원점, 이 주변/주변 탐색, 길찾기 출발, AI 추천, 완속·포트 필터.
- 별도 페이지·지도 위 모달 없음. 「지도에서 보기」만 기존 시트 전환.

### 결정
- QnA는 마이페이지에 둔다. 지도 기본 화면에는 올리지 않음(칩·검색과 겹침).
- 로그인·찜 등 자명한 항목은 제외. 문구는 현재 동작 기준.

### 다음
- 마이페이지에서 질문 펼침·지도에서 보기 확인. 항목 추가 시 helpFaqs.ts만.

## 2026-08-18 — 사용 안내를 별도 패널로

### 한 일
- 마이페이지에서 QnA 아코디언을 빼고 「사용 안내」행 → HelpGuidePanel.
- 하단 탭은 그대로. 뒤로 마이페이지, 지도에서 보기 시 패널도 닫음.
- 질문은 카드 단위. 펼치기 문구 대신 화살표.

### 결정
- 읽기 화면은 마이페이지 하위 패널. 6번째 탭·지도 덮개 모달은 안 씀.

### 다음
- 마이페이지 → 사용 안내 → 질문 펼침·뒤로·지도에서 보기 확인.

## 2026-08-18 — 포인트·결제 명칭 / 내역 UI / 뒤로가기

### 한 일
- 명칭: 지도 CTA 「충전 요청」→「이용 결제」(확정 버튼은 「결제」). 패널 제목 「포인트 · 결제」. 카드로 P 산 목록은 「포인트 충전 내역」. helpFaqs 대표 차량 문구도 이용 결제에 맞춤. 하단 탭 라벨은 짧게 「포인트」 유지.
- 포인트 홈에서 아래 펼치기 내역 제거. 잔액 카드 「내역 ›」→ PointsHistoryPanel(사용 안내와 같은 하위 패널).
- 내역 화면 mock: 탭 「이용」|「포인트 충전」. 이용=충전소·호·kWh·−P, 포인트 충전=원→P 영수증(paid/failed). 자막에 화면 예시·서버 내역 아님, 이용은 앱 장부(현장 충전 아님).
- 뒤로가기: 로그인 성공 이동 assign→replace. 토큰 있으면 /login에서 지도로 replace. 내역 패널은 pushState+popstate로 기기 뒤로가기가 패널만 닫음.

### 결정
- 예약은 1차 안 함. 공공 ev_charger_status를 예약/결제로 변조하지 않음. 앱끼리 홀드·방문 내역은 세이프차지 컨셉과 무관하고 결제 데모보다 설득력 약함. 마이페이지 방문 내역으로 빼지 않음.
- 내역은 원장 한 줄(포인트 이동) 탭을 두지 않음. 「포인트 충전 내역」(payments, 돈 넣을 때)과 「이용 내역」(usage_orders, 쓸 때)로 분리. 3탭·홈 상단 토글·한 스크롤 목록은 안 씀. 홈=잔액+충전 폼, 목록은 내역 ›.
- 로그인 페이지 인증 로직(JWT·/me·소셜)은 유지. 시트로 폼을 옮기는 건 후속. 이악물고 브라우저 뒤로가기로 사이트 나가는 건 막지 않음. 지도 본편에 pushState 가로채기 안 함.
- 남은 큰 줄기: 결제 버튼→usage_orders 4스텝, 성공 줄이 이용 내역에 쌓이게. mock은 연동 때 실데이터로.

### 다음
- 「진행해」 시 api.ts에 usage-orders 붙이고 결제 CTA 연결. BE ev_charger_status 변조는 막히면 최소 수정·승인. 로그인 시트화·예약·날씨는 후속/옵션.
## 2026-08-18 — 이용 결제 데모 합의 (공공 불변 / 가짜 장부)

### 한 일
- FE: 이용 결제 4스텝(request→pre-authorize→complete→pay), 한도 P, 카드 성공 메시지. 내역 화면 자동 이동 없음.
- BE: usage_orders가 ev_charger_status를 쓰지 않음(대기 여부 읽기만).

### 결정
- 진짜 테이블(info / 요금표 / status)은 우리 BE가 UPDATE하지 않음. 갱신은 수집 API만.
- 가짜 장부(usage_orders·지갑)는 데모. 실서비스면 정산 축을 다시 짠다. 빠진 busi_id는 그때 문의·수집.
- 요금 조회 폴백: complete가 요금표 member 행이 없거나 busi_id 공백이면 __AVG__ 단가만 읽는다. 기 행을 채우지 않음. 주문 busi_id를 __AVG__로 덮지 않음. 폴백 시 BE 로그.
- 이용 내역 탭은 confirmed(pay 끝난 건)만. draft 홀드는 숨김.
- 유저 내역 취소 버튼 없음. usage_orders cancel(홀드 롤백)은 후속. 공공 status 원복 없음.

### 다음
- complete __AVG__ 조회 폴백 + 로그. fetchUsageOrders status=confirmed.
## 2026-08-18 — 이용 결제 1차 마감 (UX·우려)

### 한 일
- 4스텝 FE, 공공 status 쓰기 제거, complete __AVG__ 단가 폴백+로그, 이용 list confirmed.
- 정산 완료 문구. 처리 중 완료=화면만 닫기. 충전가능(1+)은 비로그인도 기 목록. 이용 결제/결제는 로그인 시트.

### 결정
- 공공 테이블 BE UPDATE 금지. 가짜 장부는 데모. 실서비스면 정산 재작성.
- 유저 내역 취소 버튼 없음. cancel(홀드 롤백)은 후속.

### 우려
- HTTP 4번 직렬(느림). 완료 중 이탈 시 요청 abort 없음·연속 결제 겹칠 수 있음. cancel 없으면 draft 홀드. __AVG__ 미import 시 폴백 404.

### 다음
- usage_orders cancel. 날씨 옵션. ADMIN 회수.

## 2026-08-18 — 데모 필수 정리 (cancel·한도·날씨)

### 한 일
- 코드 없음. 작업진행상항 §10에 한도 용어·취소 UX·데모 필수·실서비스 문서만 정리.

### 결정
- 이용 「한도 P」=이번 가결제. 지갑 총잔액 상한 아님. 원→P 한 건 상한과 숫자만 같음.
- 중간·내역 취소 버튼 없음. cancel은 실패 시 홀드 전액 환불 API.
- 날씨 안 함. 데모 필수: cancel+실패 호출, 겹침 가드, ADMIN 회수.

### 다음
- 「진행해」 시 §10 필수 1→2→3.

## 2026-08-18 — usage_orders cancel (실패 롤백)

### 한 일
- POST /usage-orders/{id}/cancel (draft 홀드 전액 환불). FE는 complete/pay 실패 시에만 호출.
- payInFlightRef로 겹침 가드. _cancel_tx_key 누락 수정.

### 결정
- 내역·중간 취소 버튼 없음. 공공 status 불변.

### 다음
- ADMIN 회수.

## 2026-08-18 — 대기 기 단가 조회

### 한 일
- GET /usage-orders/rates (JWT 없음, 대기 기 member 단가). 패널 줄에 원/kWh, AVG면 추정.
- 검토 수정: router import, /rates를 /{id} 앞, 패널 훅을 컴포넌트 안, 쿼리 stat_id.

### 결정
- CSV·GET /stations 조인 없음. 대표가·요금표 UI 없음. 스켈레톤 정리는 나중.

### 다음
- ADMIN 회수.

## 2026-08-18 — 차량 내용·즐겨찾기 메모 PATCH

### 한 일
- cars `PATCH /updateCar/{id}` (번호·포트·커스텀명). FE CarPanel 수정 모드.
- favorites `PATCH /{station_id}` 메모. 목록 인라인 저장. toggle 메모는 신규만.

### 결정
- 기종 마스터 교체는 삭제 후 재등록. 대표는 setPrimary 유지.
- getPayment 회수 패널은 실서비스. 데모는 `/credit` 음수(후속, 0 하한).

### 다음
- ADMIN `/credit` 음수.

## 2026-08-18 — 현행 기준 문서 동기화 + ADMIN /credit 음수

### 한 일
- POST /points/credit: ADMIN만 ±1~100만P (0 불가). 음수는 지갑 0 하한, 실제 깎인 액만 원장. payments 불변. 일반 유저 403·UI 없음.
- FE PointsPanel: ADMIN 폼만 선행 마이너스·차감 프리셋. 일반 충전(PortOne)은 +만.
- 합의서 §0 현행 기준. 작업진행상항 데모 필수 마감. web/api README를 현재 제품에 맞춤.
- docs/teamdeveloper.md를 web/docs 전문으로 복구한 뒤 이 블록을 세 곳에 동기화.

### 결정
- 일반 유저는 /credit 조건이 풀리지 않음(role 가드). 음수는 ADMIN 조정용이며 PG 환불이 아님.
- getPayment 회수 패널은 실서비스 유지. 날씨·예약·스켈레톤 정리는 안 함/나중.
- 7월 합의서 본문은 스냅샷으로 두고, 에이전트 기준은 §0 + router.py.

### 다음
- 데모 필수 코드는 끝. 실서비스 축은 작업진행상항 §10 문서만.

## 2026-08-18 — PortOne 콘솔 취소 동기화 제외

### 한 일
- 코드 없음. 작업진행상항 §8.3을 회수 설계서에서 제외 결정으로 교체. 합의서 §0·주요확인 반영.

### 결정
- 콘솔 카드 취소 후에도 앱 paid +P가 남을 수 있다. 이 프로젝트에서 막지 않음.
- 취소 웹훅 분기, PortOne 취소 로그 동기화, getPayment 회수 패널은 구현·지시 금지. 데모는 실금 미인출인데 상시 서버·대사가 필요해 공정이 과다.
- ADMIN /credit 음수는 수동 지갑 조절. PG 환불·콘솔 취소 회수가 아님.

### 다음
- 없음 (이 구멍은 범위 밖).

## 2026-08-18 — README 서비스 소개 갱신

### 한 일
- web/README.md, api/README.md를 현행 제품 기준으로 다시 씀. 개발 정보는 Tech stack·실행·env 이름만.
- 서비스 소개: 도착 시 충전 가능성, 지도/계정/포인트/이용결제 데모. 예약·날씨·상용 정산은 범위 밖으로 명시.

### 결정
- README에 빈 스켈레톤 도메인(weather/traffic/parking/admin/history)을 기능처럼 적지 않음.
- 폴더 삭제는 이번 작업에 포함하지 않음. 정리는 별도 승인.

### 다음
- 스켈레톤 도메인 삭제 여부는 팀 확인 후.

## 2026-08-18 — 미사용 스켈레톤 도메인 제거

### 한 일
- weather / traffic / parking / admin / history 빈 라우터 삭제.
- `api/app/main.py`에서 import·`include_router` 제거.

### 결정
- 엔드포인트 없는 스켈레톤은 유지하지 않음. 관리자는 points ADMIN `/credit`, 내역은 `usage_orders`·`points`.
- FE parking UI 헬퍼는 충전소 응답용이며 이 API와 무관.

### 다음
- 없음.

## 2026-08-19 — 즐겨찾기 목록 정렬 버튼

### 한 일
- FavoritesPanel 목록 탭에 최신순/이름순 토글 버튼 추가.
- favoriteStore가 GET /favorites/list?sort=recent|name 을 그대로 사용.

### 결정
- 드롭다운 없이 버튼 한 번으로 전환. 기본값은 최신순.

### 다음
- 없음.

## 2026-08-19 — 즐겨찾기 목록 메모 UI

### 한 일
- 목록 행에서 상시 입력+저장 폼을 없앰. 없으면 「메모 추가」, 있으면 본문+「수정」.
- 편집 중에만 입력·취소·저장. 모바일 입력 16px·터치 높이 유지, iOS 포커스 줌 방지.

### 결정
- 플레이스홀더는 편집 중에만 보임. 빈 입력칸을 목록 기본 상태로 두지 않음.

### 다음
- 없음.

## 2026-08-19 — stations lat/lng 범위 검증

### 한 일
- GET /api/v1/stations Query: lat -90~90, lng -180~180. 범위 밖은 FastAPI 422.
- api/docs·web/docs stations_api.md 반영.

### 결정
- 앱 정상 좌표는 영향 없음. 검사 항목(lat=999)만 거절.

### 다음
- 없음.

## 2026-08-19 — AI 상세 카드 거리: 추천 distanceM

### 한 일
- StationDetailCard: AI 추천 활성 중이고 해당 statId의 distanceM이 있으면 그 값(m/1000)을 「직선 km」에 표시.
- 일반 지도: API `distanceKm`이 없어도(반경 밖·단건 hydrate) 현위치/stationsAnchor와 충전소 좌표로 Haversine 표시.

### 결정
- 분기만. 모델 점수/순위는 그대로. TMAP 경로 거리와 무관.
- 반경 밖 거리는 DB 재조회 없이 FE 좌표 계산. nearby SQL은 반경 내만 distance_km를 줌.

### 다음
- 실기기: AI 목록 km와 상세 「직선 km」가 같은지, 반경 밖 충전소 상세에 직선 km가 뜨는지 확인.
## 2026-08-19 — 이용 내역 충전소명 조인

### 한 일
- usage_orders 목록·단건에 ev_charger_info.stat_nm을 LEFT JOIN으로 붙여 응답(statNm).
- 내역 UI는 statNm을 쓰고, 없으면 statId로 표시.

### 결정
- usage_orders 테이블에 이름을 저장하지 않음. info 조회 시점 명칭 사용.

### 다음
- 없음.

## 2026-08-19 — 상태 오래됨(충전기 last_updated)

### 한 일
- 상세·목록·충전 요청 패널에 status.last_updated 기준 경고. 멘트는 「상태 오래됨」(사용이력 아님).
- 임계 15일. 소 단위는 충전기 행 집계: 전부 오래됨=목록 칩+상세 전체 문구, 일부만=상세만, 충전기 선택 행에 개별 표시.

### 결정
- 574건은 ev_charger_status 충전기 기준. 소 전체 테두리/마커 경고는 넣지 않음.
- last_updated null은 15일 버킷과 섞지 않음.

### 다음
- 소 단위 건수 확인 후 마커 ! 여부 재검토.

## 2026-08-20 — 충전 결제 슬라이스 3 (금액/사용량 모드 정산)

### 한 일
- BE usage_orders: pre_authorize/complete/pay에 amount|usage 모드 반영. 사용량 모드는 잔액 홀드·캡 제거·부족분 402. 금액 모드는 floor(kWh×rate)≤P 산정.
- schema/controller/service 정리(붙여넣기 메모 제거). shortfall_krw 응답 필드.
- FE api.ts: mode 전달, ApiHttpError(status), shortfallKrw 타입. StationDetailCard: 금액 탭 활성, pay 402 시 cancel 생략.

### 결정
- amount pre-auth는 사용자 입력 P, usage는 min(잔액, MAX_HOLD). pay 402는 draft 유지(충전 유도는 슬라이스 4).

### 다음
- pytest 로컬 venv에서 TC-014~020 재실행. PortOne 부족분 충전 UI(슬라이스 4).

## 2026-08-20 — 충전 결제 슬라이스 3 검토

### 한 일
- 금액/사용량 정산 경로 검토: BE pre_authorize·complete·pay, FE handleUsagePay(mode 전달, pay 402 시 cancel 생략), api.ts mode/ApiHttpError.
- 기존 TC-014~020에 mode 인자 맞춤. usage 잔액 홀드, 캡 없음+pay 402(draft 유지), amount complete kWh 무시 테스트 추가.

### 결정
- 금액 탭: 사용자 입력 P가 홀드(고정 5천 아님). 사용량 탭: 잔액 홀드, 요금은 입력 kWh×단가.
- pay 402는 draft 유지. 부족분 PortOne 충전 UI는 슬라이스 4.

### 다음
- 로컬 venv에서 `pytest tests/test_usage_orders.py`. 슬라이스 4: 402 시 포인트 충전 유도.
## 2026-08-20 — draft 이용주문 복구 (새로고침·재로그인)

### 한 일
- FE etchUsageOrders(limit, status) — draft 목록 조회. usageDraftStore.hydrate() 로 최신 draft 1건 보관.
- /map 로그인 후 handlePostLoginLanding: draft 있으면 해당 충전소 setSelectedId.
- StationDetailCard: draft·선택 충전소 일치 시 chargeMode·pendingOrderId·shortfall UI 복구. 결제 취소(dismissPendingOrder)·성공 시 store clear.
- pay 402 재시도 버튼: pending 있으면 canPay 없이 결제 가능.

### 결정
- BE 변경 없음 — GET /usage-orders/list?status=draft&limit=1 재사용.
- complete 전 draft(홀드만)는 취소 버튼만; 요금 산정 후(shortfall) 충전 UI.

### 다음
- 수동: 402 → 새로고침 → 해당 충전소 카드에서 이어하기/취소 확인.
