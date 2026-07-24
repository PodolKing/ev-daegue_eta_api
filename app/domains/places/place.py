from pydantic import BaseModel


class PlaceResult(BaseModel):
    id: str
    name: str
    address: str
    lat: float
    lng: float