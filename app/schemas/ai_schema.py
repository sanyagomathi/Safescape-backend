from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AIHomeInsightsOut(BaseModel):
    summary: str
    stats: Dict[str, Any]
    highlights: List[str]


class AIChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    lat: float
    lng: float
    radius_km: float = Field(2.0, ge=0.1, le=10.0)
    hour: Optional[int] = Field(None, ge=0, le=23)


class AIChatOut(BaseModel):
    reply: str
    context: Dict[str, Any]