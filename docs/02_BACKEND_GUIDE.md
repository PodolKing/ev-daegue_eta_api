# EV SafeCharge 백엔드 작업 가이드

> 대상: 백엔드 담당 1명  
> 기술 예시: Express + TypeScript + Prisma  
> 현재 단계: 공공데이터 원본을 바로 완벽하게 DB화하기보다 목데이터로 API 계약과 서버 흐름을 먼저 완성

## 1. 이번 작업의 목표

백엔드의 첫 번째 목표는 모든 외부 API를 한 번에 연결하는 것이 아닙니다.

**프론트엔드가 사용할 수 있는 충전소 목록·상세·추천 API를 목데이터로 먼저 제공하고, 나중에 내부 데이터 출처만 실제 DB와 수집 데이터로 교체하는 것**이 목표입니다.

```text
목데이터 또는 시드 파일
→ 서비스 함수
→ API 라우터
→ 프론트에 고정된 JSON 반환
→ 실제 DB 연결 후 서비스 함수 내부만 교체
```

## 2. 전달받아야 하는 파일

| 파일 | 용도 |
|---|---|
| `shared/types.ts` | API 응답 타입 기준 |
| `backend/stations.seed.ts` | 서버에서 바로 사용할 충전소 시드 데이터 |
| `json/stations.json` | 목록 응답 예시 |
| `json/station-detail-MOCK-ST001.json` | 상세 응답 예시 |
| `json/recommendations.json` | 추천 응답 예시 |
| `json/api-errors.json` | 공통 오류 응답 예시 |
| `docs/API_CONTRACT.md` | API 경로와 기본 계약 |

## 3. 권장 폴더 구조

```text
apps/api/src/
├─ app.ts
├─ server.ts
├─ routes/
│  ├─ health.routes.ts
│  ├─ station.routes.ts
│  └─ recommendation.routes.ts
├─ controllers/
│  ├─ station.controller.ts
│  └─ recommendation.controller.ts
├─ services/
│  ├─ station.service.ts
│  └─ recommendation.service.ts
├─ repositories/
│  └─ station.repository.ts
├─ mocks/
│  └─ stations.seed.ts
├─ types/
│  └─ station.ts
├─ middlewares/
│  ├─ errorHandler.ts
│  └─ notFoundHandler.ts
└─ utils/
   └─ apiResponse.ts
```

비전공자 팀에서는 처음부터 계층을 너무 복잡하게 만들지 않아도 됩니다. 다만 라우터 안에 모든 코드를 넣지는 말고 최소한 `route → service`는 분리합니다.

## 4. 작업 순서

### 1단계: 서버 실행과 헬스체크

구현 API:

```http
GET /health
```

응답:

```json
{
  "status": "ok",
  "service": "ev-safecharge-api",
  "mode": "mock"
}
```

완료 조건:

- 서버 실행 성공
- Postman 또는 브라우저에서 상태코드 200 확인
- 환경변수 없이도 개발 모드 실행 가능

권장 브랜치명:

```text
feature/be-station-api
```

### 2단계: 충전소 목록 API

구현 API:

```http
GET /api/stations
```

초기에는 `stations.seed.ts`를 반환합니다.

```ts
import { stationSeed } from '../mocks/stations.seed';

export function findStations() {
  return stationSeed;
}
```

라우터 예시:

```ts
router.get('/', async (_req, res, next) => {
  try {
    const stations = await stationService.findStations();
    res.status(200).json(stations);
  } catch (error) {
    next(error);
  }
});
```

### 3단계: 목록 필터와 정렬

처음 구현할 쿼리:

| 쿼리 | 예시 | 동작 |
|---|---|---|
| `chargerType` | `급속` | 해당 타입 포함 충전소만 조회 |
| `availableOnly` | `true` | 사용 가능 충전기 1대 이상 |
| `sort` | `distance` | 거리순 정렬 |
| `sort` | `available` | 사용 가능 대수순 정렬 |

예시:

```http
GET /api/stations?chargerType=급속&availableOnly=true&sort=available
```

값이 잘못된 경우 400 오류를 반환합니다.

### 4단계: 충전소 상세 API

구현 API:

```http
GET /api/stations/:stationId
```

초기에는 `MOCK-ST001`의 상세 JSON 구조를 사용합니다.

존재하지 않는 ID:

```json
{
  "code": "STATION_NOT_FOUND",
  "message": "충전소를 찾을 수 없습니다.",
  "isMock": true
}
```

상태코드: `404`

### 5단계: 추천 API

구현 API:

```http
GET /api/recommendations
```

초기에는 `recommendations.json`을 반환합니다.

선택 쿼리:

- `lat`
- `lng`
- `radius`
- `arrivalAt`

현재 모델이 없더라도 API는 작동해야 합니다.

```ts
export async function getRecommendations() {
  return mockRecommendations;
}
```

이후 데이터 담당의 규칙 함수가 준비되면 내부만 바꿉니다.

```ts
export async function getRecommendations(input) {
  const stations = await stationRepository.findCandidates(input);
  return recommendationEngine.rank(stations, input);
}
```

### 6단계: 오류 응답 통일

모든 오류는 같은 형식을 사용합니다.

```ts
type ApiErrorResponse = {
  code: string;
  message: string;
  details?: unknown;
  fallback?: string;
  isMock?: boolean;
};
```

필수 오류:

| 상태 | 코드 | 상황 |
|---|---|---|
| 400 | `INVALID_COORDINATES` | 위도·경도 형식 오류 |
| 404 | `STATION_NOT_FOUND` | 충전소 없음 |
| 503 | `EXTERNAL_API_UNAVAILABLE` | 외부 API 장애 |
| 500 | `INTERNAL_SERVER_ERROR` | 예상하지 못한 서버 오류 |

### 7단계: CORS와 환경변수

개발 환경 예시:

```env
PORT=4000
FRONTEND_ORIGIN=http://localhost:3000
DATA_MODE=mock
```

환경변수 원칙:

- API 키를 코드에 직접 작성하지 않음
- `.env`는 Git에 올리지 않음
- `.env.example`에는 변수명만 작성
- 개발용과 배포용 주소를 구분

### 8단계: 실제 공공데이터 변환 계층

공공데이터 원본 필드를 프론트에 그대로 보내지 않습니다.

```ts
export function toStationSummary(raw: RawPublicStation): StationSummary {
  return {
    stationId: raw.statId,
    stationName: raw.statNm,
    address: raw.addr,
    latitude: Number(raw.lat),
    longitude: Number(raw.lng),
    totalChargers: raw.totalCount,
    availableChargers: raw.availableCount,
    chargingChargers: raw.chargingCount,
    unavailableChargers: raw.unavailableCount,
    chargerTypes: mapChargerTypes(raw),
    operator: raw.busiNm ?? '미확인',
    available24Hours: mapOperationTime(raw),
    parkingFee: mapParkingFee(raw),
    updatedAt: toIsoDate(raw.statUpdDt),
    dataFreshnessMinutes: calculateFreshness(raw.statUpdDt),
    distanceKm: null,
    etaMinutes: null,
    isMock: false,
  };
}
```

실제 필드명이 확정되지 않은 부분은 데이터 담당과 합의해서 수정합니다.

### 9단계: DB 테이블 초안

최소 테이블:

```text
stations
chargers
charger_status_history
```

관계:

```text
stations 1 --- N chargers
chargers 1 --- N charger_status_history
```

권장 핵심 컬럼:

#### stations

- `station_id`
- `station_name`
- `address`
- `latitude`
- `longitude`
- `operator`
- `parking_fee`

#### chargers

- `charger_id`
- `station_id`
- `charger_type`
- `connector_type`
- `capacity_kw`

#### charger_status_history

- `id`
- `charger_id`
- `status`
- `status_updated_at`
- `observed_at`

중요: `status_updated_at`은 공공 API에서 알려준 상태 갱신시각이고, `observed_at`은 우리 시스템이 수집한 시각입니다. 서로 다른 값입니다.

### 10단계: 목데이터와 실제 데이터 모드 분리

```ts
const mode = process.env.DATA_MODE ?? 'mock';

export async function findStations() {
  if (mode === 'mock') {
    return stationSeed;
  }

  return stationRepository.findAll();
}
```

프론트 입장에서는 모드가 바뀌어도 응답 구조가 동일해야 합니다.

## 5. GitHub 이슈 분리 예시

### BE-01 서버 실행과 헬스체크

- Express 서버 실행
- `/health` 구현
- 오류 없는 종료 처리

### BE-02 목록 API 구현

- `stations.seed.ts` 연결
- `/api/stations` 구현
- 필터와 정렬 추가

### BE-03 상세 API 구현

- `/api/stations/:stationId`
- 404 오류 처리
- 상세 JSON 반환

### BE-04 추천 API 구현

- `/api/recommendations`
- 목 추천 결과 반환
- 입력값 검증

### BE-05 공통 오류 처리

- 오류 응답 타입 통일
- 400, 404, 500, 503 테스트

### BE-06 실제 데이터 변환 함수

- 공공데이터 원본 → `StationSummary`
- 시간 형식 ISO 8601 변환
- 숫자 문자열 형변환

## 6. API 테스트 체크리스트

- [ ] `GET /health`가 200을 반환한다.
- [ ] `GET /api/stations`가 배열을 반환한다.
- [ ] 목록의 모든 항목에 `stationId`가 있다.
- [ ] `availableOnly=true`가 정상 작동한다.
- [ ] 존재하지 않는 상세 ID가 404를 반환한다.
- [ ] 추천 API 결과에 `rank`, `riskLevel`, `recommendReasons`가 있다.
- [ ] 날짜는 ISO 8601 형식이다.
- [ ] 서버 오류가 HTML이 아닌 JSON으로 반환된다.
- [ ] 프론트 주소에 CORS가 허용된다.

## 7. 1차 완료 기준

다음을 모두 만족하면 백엔드 1차 작업 완료입니다.

- [ ] `/health`, `/api/stations`, `/api/stations/:stationId`, `/api/recommendations`가 작동한다.
- [ ] 목데이터를 반환하지만 응답 타입이 고정되어 있다.
- [ ] 400·404·500·503 오류 형식이 통일되어 있다.
- [ ] 프론트에서 목록 API를 호출해 화면에 표시할 수 있다.
- [ ] `DATA_MODE=mock` 구조가 준비되어 있다.
- [ ] 공공데이터 원본을 변환할 함수 위치가 정해져 있다.
- [ ] API 명세가 README 또는 Swagger에 기록되어 있다.

## 8. 데이터 파트에 요청할 내용

백엔드 담당자는 데이터 파트에 다음 자료를 요청합니다.

- 상태코드 원본값과 표준값 매핑표
- 충전소 ID와 충전기 ID 정의
- 결측값 처리 원칙
- 기준시각과 수집시각 구분
- 추천 함수 입력 필드
- 추천 함수 출력 타입
- 공백 발생 시 이전 상태 유지 여부

## 9. 하지 않아도 되는 작업

현재 단계에서는 아래 작업을 미뤄도 됩니다.

- 전체 외부 API 동시 연동
- 복잡한 인증과 권한
- 대규모 캐시 최적화
- 실시간 교통 장애까지 완벽한 처리
- AI 모델 직접 학습
- 운영 수준의 모니터링 시스템

먼저 **고정된 API 계약과 프론트 연결 성공**을 목표로 하세요.
