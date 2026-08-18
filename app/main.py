from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.domains.auth.router import router as auth_router
from app.domains.cars.router import router as cars_router
from app.domains.places.router import router as places_router
from app.domains.points.router import router as points_router
from app.domains.recommendations.router import router as recommendations_router
from app.domains.stations import sync as stations_sync
from app.domains.stations.router import router as stations_router
from app.domains.stations.sync import _ensure_sync_logging
from app.domains.routes.router import router as routes_router
from app.domains.favorites.router import router as favorites_router
from app.domains.usage_orders.router import router as usage_orders_router

settings = get_settings()
_ensure_sync_logging()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    stations_sync.start_scheduler()
    try:
        yield
    finally:
        stations_sync.stop_scheduler()


app = FastAPI(
    title="EV SafeCharge API",
    description="대구 EV 세이프차지 — stations / auth / points",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}


app.include_router(stations_router)
app.include_router(auth_router)
app.include_router(cars_router)  # 내 차량 조회·등록·소프트 삭제
app.include_router(points_router)
app.include_router(recommendations_router)
app.include_router(places_router)
app.include_router(routes_router)
app.include_router(favorites_router)
app.include_router(usage_orders_router)  # 충전 가결제·요금 정산

