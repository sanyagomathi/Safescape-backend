from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...db import get_db
from ...models import Score
from ...schemas.score_schema import ScoreOut

router = APIRouter(prefix="/scores", tags=["scores"])

@router.get("/{segment_id}/{hour}", response_model=ScoreOut)
def get_score(segment_id: str, hour: int, db: Session = Depends(get_db)):
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="hour must be 0..23")

    score = db.execute(
        select(Score).where(Score.segment_id == segment_id, Score.hour == hour)
    ).scalar_one_or_none()

    if score is None:
        return ScoreOut(
            segment_id=segment_id,
            hour=hour,
            overall=0.5,
            women=None,
            confidence=0.2,
            anomaly=False,
        )

    return ScoreOut(
        segment_id=score.segment_id,
        hour=score.hour,
        overall=float(score.overall),
        women=(float(score.women) if score.women is not None else None),
        confidence=float(score.confidence),
        anomaly=bool(score.anomaly),
    )