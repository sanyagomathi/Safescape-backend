from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...db import get_db
from ...models import Review, Segment, Score
from ...schemas.review_schema import ReviewCreate, ReviewOut
from ...services.scoring import compute_score

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("", response_model=ReviewOut)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)):
    # Ensure segment exists (MVP rule)
    seg = db.execute(select(Segment).where(Segment.id == payload.segment_id)).scalar_one_or_none()
    if seg is None:
        # For MVP you can also auto-create segments; but safer to require it exists
        # to avoid garbage segment_ids.
        raise ValueError("segment_id not found. Create/seed segments first.")

    r = Review(
        segment_id=payload.segment_id,
        category=payload.category,
        gender=payload.gender,
        hour=payload.hour,
        rating=payload.rating,
        note=payload.note,
    )
    db.add(r)
    db.commit()
    db.refresh(r)

    # Recompute score cache for this segment+hour (MVP: last 30 days not enforced here)
    rows = db.execute(
        select(Review.rating, Review.gender).where(
            Review.segment_id == payload.segment_id,
            Review.hour == payload.hour,
        )
    ).all()
    review_list = [{"rating": float(rt), "gender": gd} for (rt, gd) in rows]

    signals = {
        "lighting": float(seg.lighting),
        "crowd": float(seg.crowd),
        "shops_open": float(seg.shops_open),
        "transport": float(seg.transport),
    }
    score_dict = compute_score(hour=payload.hour, signals=signals, reviews=review_list)

    # Upsert into Score table
    score = db.execute(
        select(Score).where(Score.segment_id == payload.segment_id, Score.hour == payload.hour)
    ).scalar_one_or_none()

    if score is None:
        score = Score(
            segment_id=payload.segment_id,
            hour=payload.hour,
            overall=score_dict["overall"],
            women=score_dict["women"],
            confidence=score_dict["confidence"],
            anomaly=score_dict["anomaly"],
        )
        db.add(score)
    else:
        score.overall = score_dict["overall"]
        score.women = score_dict["women"]
        score.confidence = score_dict["confidence"]
        score.anomaly = score_dict["anomaly"]

    db.commit()
    return r