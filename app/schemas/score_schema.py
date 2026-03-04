from pydantic import BaseModel

class ScoreOut(BaseModel):
    segment_id: str
    hour: int
    overall: float
    women: float | None
    confidence: float
    anomaly: bool