from fastapi import APIRouter

from app.domains.routes.schema import CarRouteRequest, CarRouteResponse
from app.domains.routes.services import get_car_route

router = APIRouter(
    prefix="/api/v1/routes",
    tags=["routes"],
)


@router.post("/car", response_model=CarRouteResponse)
async def car_route(body: CarRouteRequest) -> CarRouteResponse:
    return await get_car_route(body)
