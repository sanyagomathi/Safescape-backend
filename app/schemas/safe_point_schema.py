from pydantic import BaseModel

class SafePointOut(BaseModel):
    id: int
    name: str
    category: str
    lat: float
    lng: float
    phone: str
    is_24x7: bool

    class Config:
        from_attributes = True