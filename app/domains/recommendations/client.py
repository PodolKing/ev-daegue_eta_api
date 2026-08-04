import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from app.core.config import get_settings
from app.domains.recommendations.schema import RecommendRequest, RecommendResponse
def _to_upstream_payload(body: RecommendRequest) -> dict:
    return body.model_dump(by_alias=False, exclude_none=True)
async def fetch_recommendations(body: RecommendRequest) -> RecommendResponse:
    s = get_settings()
    if not s.recommend_api_key:
        raise HTTPException(status_code=503, detail="RECOMMEND_API_KEY not configured")
    url = f"{s.recommend_api_base_url.rstrip('/')}/api/v1/chargers/recommend"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": s.recommend_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=s.recommend_api_timeout) as client:
            r = await client.post(url, json=_to_upstream_payload(body), headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="추천 서버 응답 지연")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=500, detail="추천 서버 인증 실패 — API 키 확인")
        raise HTTPException(status_code=502, detail=f"추천 서버 오류: {e.response.status_code}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"추천 서버 통신 실패: {e}")
    # 디버그: 터미널에 업스트림 원문 확인
   
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail=f"추천 서버 응답이 object가 아님: {type(data).__name__}",
        )
    try:
        return RecommendResponse.model_validate(data)
    except ValidationError as e:
        raise HTTPException(status_code=502, detail=f"응답 스키마 불일치: {e}") from e
