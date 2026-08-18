# EV SafeCharge 최종 검토

> 협의 마감: **2026-08-18**  
> 정본: 합의서 §0 · `작업진행상항.md`(로컬) · 각 도메인 `router.py`  
> 추가 기능은 **재협의 후**. 시크릿·실키 없음.  
> Cursor 화면본: 워크스페이스 `canvases/final-review.canvas.tsx` (Cursor에서만 렌더)

이 범위는 **마무리해도 된다.** 1개월 Must와 데모 필수 코드 3항은 들어갔다. PortOne 콘솔 취소 ↔ 앱 포인트 동기화는 빼기로 했다.

| 항목 | 값 |
|---|---|
| 1개월 Must | 충족 |
| 데모 필수 (코드) | **3 / 3** |
| 지금 구현 공백 | **0건** |
| 추가 기능 | 재협의 |

제품 줄기: 지도·인증·찜·차·마이페이지·PortOne 충전·이용결제·cancel·`/credit` ± 는 완료. PortOne 콘솔 취소 동기화·날씨·예약은 안 함.

Git 복사본: `web/docs/final_review.md`, `api/docs/final_review.md`

---

## 마감 체크

| 상태 | 항목 |
|---|---|
| 됨 | 데모 필수 3항 — cancel(실패 롤백), 겹침 가드, ADMIN `/credit` ± (0 하한, 일반 유저 403·UI 없음) |
| 됨 | 합의서 §0, README, teamdeveloper 세 곳 동기화. 현행 제품이 기준 |
| 안 함 | PortOne 콘솔 취소 ↔ 앱 P 동기화. 취소 웹훅·getPayment 회수 구현 금지. `/credit`은 수동 지갑 조절이지 PG 환불이 아님 |
| 안 함 | 날씨 · 예약 · 스켈레톤 정리. 넣으려면 재협의 |
| 확인만 | DB에 요금표 member `__AVG__` 행 import 여부 (코드 아님) |

---

## 데모 필수 3항

| 항목 | 상태 | 내용 |
|---|---|---|
| cancel + 실패 호출 | 됨 | `POST /usage-orders/{id}/cancel`. FE는 complete/pay 실패 시에만. 중간·내역 취소 버튼 없음 |
| 겹침 가드 | 됨 | `payInFlightRef`. 처리 중 화면 닫기는 abort 없음(허용). 탭 강제종료 시 cancel 미호출은 데모 한계 |
| `/credit` ± | 됨 | ADMIN만 ±1~100만 P, 차감은 잔액 0 하한. payments 불변. 일반 유저 PortOne 충전은 +만 |

---

## 1개월 토이 vs 지금

| 항목 | 7월 합의 | 8/18 마감 |
|---|---|---|
| TMAP + stations | DB 반경, `availableCount` null≠0 | 됨. UI 반경 1/2/3km (동결) |
| 로그인 + me | 외부 1종 | 로컬 + 카카오/구글/네이버, JWT `/me` |
| 포인트 | A 테스트 또는 B PG | PortOne B안 + ADMIN `/credit` ± |
| 즐겨찾기·차량·마이페이지 | Should / 후속 | 됨 (기종 마스터 교체 없음) |
| 이용 결제 | Out (상용 정산) | `usage_orders` 4스텝 데모. 공공 status 읽기만 |
| 콘솔 취소 ↔ 앱 P | (없음) | **안 함.** 실금 미인출 대비 대사 공정 과다 |

---

## 안 함 (재협의 전 구현 금지)

| 항목 | 이유 |
|---|---|
| 날씨 | 버튼 비활성. API 연결 안 함 |
| 예약 | 공공 status 변조 금지 |
| PortOne 취소 동기화 | 웹훅 분기·getPayment·상시 서버 필요 |
| 로그인 시트화 | JWT·`/me` 유지 |
| 비밀번호 PATCH · 탈퇴 CASCADE | 소셜 password NULL · 소프트 삭제 |
| weather/traffic 스켈레톤 정리 | 나중 |

### 데모 한계 (고치지 않고 마감)

| 한계 | 영향 |
|---|---|
| 이용 HTTP 4번 직렬 | 느림. 단축 없음 |
| 탭 종료 시 cancel 없음 | draft 홀드 남을 수 있음 |
| 콘솔 취소 후 +P 유지 | 의도. `/credit`은 수동 조절만 |

---

## 문서 역할

에이전트 기준은 **합의서 §0**과 **`router.py`**. 7월 본문은 스냅샷. README와 teamdeveloper 세 곳은 현행에 맞춰 두었다.

| 문서 | 역할 |
|---|---|
| 합의서 §0 (`docs/프로젝트_현황_및_합의사항_20260723.md`) | 지금 제품 한 장 |
| `작업진행상항.md` | 로컬 세션 메모. git 아님. API 정본 아님 |
| `docs/teamdeveloper.md` (+ `web/docs`, `api/docs`) | 팀 로그 |
| `web/README.md` · `api/README.md` | 공개 소개. 키 이름만 |
| 각 도메인 `router.py` | HTTP 경로 정본 |

---

## 7월 합의와 다른 점 (후속 합의로 덮임)

| 원래 | 현재 |
|---|---|
| UI 반경 3/5/10km, 기본 3km | 1/2/3km, FE 기본 1km, 고정 줌 |
| 포인트 A안 `charge-test` | PortOne + ADMIN `/credit` ± |
| 원장 탭 | 이용 `confirmed` + `payments`만 |
| 추천 AIR-001 사내 규칙 1차 | 외부 recommend 프록시 |
| 외부 로그인 1종 | 카카오·구글·네이버 + 로컬 |
| limit 상한 100 | BE `MAX_LIMIT` 200, 3km→150 |

---

## 이용 정산 — 실서비스면 재작성

지금 구현 금지. `작업진행상항.md` §10.

가짜 `usage_orders`를 사업자 실결제·세션 kWh에 맞게 다시 짠다. 4 HTTP를 서버 트랜잭션으로, 충전가능/이용 결제 UI 분리, 내역에 충전소 이름.

**PortOne 취소 대사는 여기에도 넣지 않는다.** 상용에서 따로 재협의.

---

마감 시나리오: 로그인 → 지도 → 잔액 → 포인트 충전 → 이용 결제.  
제외: 콘솔 취소 동기화. 추가 기능 = 재협의.
