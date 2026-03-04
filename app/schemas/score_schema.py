from pydantic import BaseModel
from typing import Optional

class ScoreOut(BaseModel):
    segment_id: str
    hour: int
    overall: float
    women: Optional[float] = None
    confidence: float
    anomaly: bool