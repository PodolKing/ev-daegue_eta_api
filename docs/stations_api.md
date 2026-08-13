# GET /api/v1/stations

## Query

| Param | Type | Default | Max | Notes |
|---|---|---|---|---|
| `lat` | number | required | — | Current latitude |
| `lng` | number | required | — | Current longitude |
| `radiusKm` | number | `3` | `10` | Straight-line radius (km). UI: **1 / 2 / 3** |
| `limit` | int | `50` | `200` | Max stations. FE: **1→50 / 2→100 / 3→200** |

Distance is **DB Haversine** (bbox → filter → sort). Not TMAP route distance.

## Response (camelCase body)

Top-level item = **station** (`stat_id` aggregate). Nested `chargers[]` = **one row per charger** (info + status).

```json
{
  "items": [
    {
      "stationId": "ST001",
      "name": "대구시청 공영주차장",
      "address": "대구광역시 …",
      "lat": 35.8714,
      "lng": 128.6014,
      "availableCount": 2,
      "availableCountOther": 1,
      "availableCountSlow": 1,
      "distanceKm": 0.84,
      "chargerTotal": 4,
      "chargerTotalOther": 3,
      "chargerTypes": ["02", "04"],
      "chargers": [
        {
          "chgerId": "01",
          "statNm": "대구시청 공영주차장",
          "chgerType": "04",
          "addr": "대구광역시 …",
          "addrDetail": null,
          "location": "B1",
          "lat": 35.8714,
          "lng": 128.6014,
          "useTime": "24시간",
          "busiId": "ME",
          "bnm": "환경부",
          "busiNm": "환경부",
          "busiCall": "1661-9408",
          "output": 50,
          "method": "단독",
          "zcode": "27",
          "zscode": "27110",
          "kind": "A0",
          "kindDetail": null,
          "parkingFree": "Y",
          "note": null,
          "limitYn": "N",
          "limitDetail": null,
          "delYn": "N",
          "delDetail": null,
          "trafficYn": "N",
          "installYear": "2020",
          "floorNum": "B1",
          "floorType": "지하",
          "infoUpdatedAt": "2026-07-01T00:00:00",
          "chargerStatus": "2",
          "lastUpdated": "2026-08-04T12:00:00"
        }
      ],
      "sourceMode": "LIVE"
    }
  ],
  "radiusKm": 3,
  "limit": 50,
  "count": 1
}
```

### `chargers[]`

| Field | Source |
|---|---|
| `chgerId` … `infoUpdatedAt` | `ev_charger_info` (row columns; `infoUpdatedAt` ← `updated_at`) |
| `chargerStatus`, `lastUpdated` | `ev_charger_status` |

`stat_id`는 상위 `stationId`와 동일하므로 중첩에 중복하지 않음.

## Rules (do not change)

- Aggregate by `stat_id` (station), not charger row (top-level item).
- `availableCount`: all chargers with `charger_status = '2'` (충전대기) — **합계** (마커·리스트용).
- `availableCountOther` / `availableCountSlow`: same rule scoped by `chgerType` (slow = `02`/`08`; other = not slow, null type → other). Detail breakdown only.
- `chargerTotal`: all chargers at station. `chargerTotalOther`: non-slow only (same type rule). No `chargerTotalSlow` — derive as `total − other` if needed.
- If no valid status observation in that bucket → that field is `null` (**null ≠ 0**).
- Status codes: `1` 통신이상 / `2` 충전대기 / `3` 충전중 / `4` 운영중지 / `5` 점검중 / `9` 상태미확인.
- Exclude rows with null `lat`/`lng`.
- Sort by `distanceKm` ascending.
- Full table dump (~25k) is forbidden.

## GET /api/v1/stations/search

즐겨찾기 추가 탭 등. **기존 GET /stations(lat/lng/radius)와 별도.** 지도 목록 계약은 변경하지 않음.

### Query

| Param | Type | Default | Max | Notes |
|---|---|---|---|---|
| `q` | string | required | 100 | 충전소명·주소 contains. **2자 이상**(trim 후 미달이면 items=[]). LIKE 와일드카드 `%` `_` 는 제거 |
| `limit` | int | `20` | `30` | 전체 dump 금지 |

`stat_nm` / `addr` / `addr_detail` 매칭. `stat_id` 집계. 좌표 null 제외. 이름순.

### Response (camelCase)

충전기 배열 없음. 요약만.

```json
{
  "items": [
    {
      "stationId": "ST001",
      "name": "대구시청 공영주차장",
      "address": "대구광역시 …",
      "lat": 35.8714,
      "lng": 128.6014,
      "availableCount": 2
    }
  ],
  "query": "시청",
  "limit": 20,
  "count": 1
}
```

`availableCount`: stations와 동일. 관측 없으면 **null**(0과 구분). `charger_status=2` 대수.

FE: `GET {API}/api/v1/stations/search?q=동성로&limit=20` 후 선택 `stationId`를 `POST /favorites/toggle`에 넘긴다. TMAP places 검색과 혼용하지 않음.
