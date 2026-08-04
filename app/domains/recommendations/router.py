"""추천 프록시 — 외부 충전소 추천 모델 API."""
from fastapi import APIRouter
from app.domains.recommendations.client import fetch_recommendations
from app.domains.recommendations.schema import RecommendRequest, RecommendResponse
router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])
@router.post("", response_model=RecommendResponse)
async def recommend(body: RecommendRequest) -> RecommendResponse:
    """
    목적지 기준 AI 추천.
    FE → 여기 → 외부 /api/v1/chargers/recommend
    """
    return await fetch_recommendations(body)

