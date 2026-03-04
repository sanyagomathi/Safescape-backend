from pydantic import BaseModel, Field

class ReviewCreate(BaseModel):
    segment_id: str = Field(..., min_length=1, max_length=64)
    category: str = Field(..., min_length=1, max_length=32)
    gender: str = Field("unknown", pattern="^(woman|man|unknown)$")
    hour: int = Field(..., ge=0, le=23)
    rating: float = Field(..., ge=0.0, le=1.0)
    note: str = Field("", max_length=280)

class ReviewOut(BaseModel):
    id: int
    segment_id: str
    category: str
    gender: str
    hour: int
    rating: float
    note: str

    class Config:
        from_attributes = True