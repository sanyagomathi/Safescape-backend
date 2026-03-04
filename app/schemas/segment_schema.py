from pydantic import BaseModel, Field

class SegmentOut(BaseModel):
    id: str
    lat: float
    lng: float
    lighting: float
    crowd: float
    shops_open: float
    transport: float

    class Config:
        from_attributes = True

class SegmentSeedRequest(BaseModel):
    center_lat: float
    center_lng: float
    count: int = Field(50, ge=1, le=2000)

    # objective signal defaults (0..1)
    lighting: float = Field(0.6, ge=0.0, le=1.0)
    crowd: float = Field(0.5, ge=0.0, le=1.0)
    shops_open: float = Field(0.5, ge=0.0, le=1.0)
    transport: float = Field(0.6, ge=0.0, le=1.0)

    # how spread out the points are around the center (meters)
    spread_m: float = Field(800.0, ge=50.0, le=5000.0)

    # optional id prefix
    id_prefix: str = Field("seg_demo_", min_length=1, max_length=32)