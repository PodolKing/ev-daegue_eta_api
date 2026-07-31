from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.history.router import router as history_router
from app.domains.parking.router import router as parking_router
from app.domains.places.router import router as places_router
from app.domains.points.router import router as points_router
from app.domains.recommendations.router import router as recommendations_router
from app.domains.stations import sync as stations_sync
from app.domains.stations.router import router as stations_router
from app.domains.traffic.router import router as traffic_router
from app.domains.weather.router import router as weather_router
from app.domains.stations.sync import _ensure_sync_logging
from app.domains.routes.router import router as routes_router

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
app.include_router(points_router)
app.include_router(recommendations_router)
app.include_router(traffic_router)
app.include_router(parking_router)
app.include_router(weather_router)
app.include_router(places_router)
app.include_router(routes_router)
app.include_router(history_router)
app.include_router(admin_router)
