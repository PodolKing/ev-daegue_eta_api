from pydantic import BaseModel


class PlaceResult(BaseModel):
    id: str
    name: str
    address: str
    lat: float
    lng: float
    # TMAP poi (client._normalize_pois). UI: lower→middle, parkFlag true만 표시.
    middleBizName: str | None = None
    lowerBizName: str | None = None
    parkFlag: bool | None = None