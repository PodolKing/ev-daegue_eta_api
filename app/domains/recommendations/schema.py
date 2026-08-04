from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Any, Literal
from app.schemas.base import CamelModel
class RecommendRequest(CamelModel):
    dest_lat: float
    dest_lng: float
    eta_minutes: float  # 1 이상
    radius_km: float | None =  2.0
    top_k: int | None = 10
    arrival_at: str | None = None
    mode: Literal["external", "home"] | None = "external"
    registered_stat_ids: list[str] | None = None
    origin_lat: float | None = None
    origin_lng: float | None = None
    current_soc: float | None = None
    vehicle_model_id: str | None = None
    min_output_kw: float | None = None
    include_slow: bool | None = False
class RecommendParking(CamelModel):
    pklt_id: str | None = None
    parking_nm: str | None = None
    total_spaces: int | None = None
    remaining_spaces: int | None = None
    occupancy_rate: float | None = None
    congestion_status: str | None = None
    fee_type: str | None = None
    is_24h: bool | None = None
class RecommendItem(CamelModel):
    rank: int | None = None
    stat_id: str
    stat_nm: str | None = None
    addr: str | None = None
    lat: float
    lng: float
    distance_m: float | None = None
    recommendation_score: float | None = None
    recommendation_label: str | None = None
    score_breakdown: dict[str, Any] | None = None
    access_coefficient: float | None = None
    avg_available_prob: float | None = None
    score: float | None = None
    detour_minutes: float | None = None
    extra_distance_km: float | None = None
    arrival_soc_pct: float | None = None
    parking: RecommendParking | None = None
class RecommendMeta(CamelModel):
    model_version: str | None = None
    request_id: str | None = None
    confidence_level: str | None = None
    radius_expanded: bool | None = None
    radius_note: str | None = None
    horizon_note: str | None = None
    remaining_model: bool | None = None
class RecommendResponse(CamelModel):
    meta: RecommendMeta | None = None
    recommendations: list[RecommendItem] = []