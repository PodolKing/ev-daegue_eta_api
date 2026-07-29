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
      "sourceMode": "LIVE"
    }
  ],
  "radiusKm": 3,
  "limit": 50,
  "count": 1
}
```

## Rules (do not change)

- Aggregate by `stat_id` (station), not charger row.
- `availableCount`: all chargers with `charger_status = '2'` (충전대기) — **합계** (마커·리스트용).
- `availableCountOther` / `availableCountSlow`: same rule scoped by `chgerType` (slow = `02`/`08`; other = not slow, null type → other). Detail breakdown only.
- `chargerTotal`: all chargers at station. `chargerTotalOther`: non-slow only (same type rule). No `chargerTotalSlow` — derive as `total − other` if needed.
- If no valid status observation in that bucket → that field is `null` (**null ≠ 0**).
- Status codes: `1` 통신이상 / `2` 충전대기 / `3` 충전중 / `4` 운영중지 / `5` 점검중 / `9` 상태미확인.
- Exclude rows with null `lat`/`lng`.
- Sort by `distanceKm` ascending.
- Full table dump (~25k) is forbidden.
