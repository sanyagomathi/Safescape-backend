import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text, select

from .db import get_db, engine, Base
from .models import Review, Score

app = FastAPI(title="Safescape Backend (MVP)")

# CORS (so website can call backend too)
origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP convenience: create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    val = db.execute(text("SELECT 1")).scalar_one()
    return {"db": val}

class ReviewIn(BaseModel):
    segment_id: str = Field(..., min_length=1, max_length=64)
    category: str = Field(..., min_length=1, max_length=32)
    gender: str = Field("unknown")
    hour: int = Field(..., ge=0, le=23)
    rating: float = Field(..., ge=0.0, le=1.0)
    note: str = Field("", max_length=280)

@app.post("/reviews")
def create_review(payload: ReviewIn, db: Session = Depends(get_db)):
    # Save review
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

    # MVP scoring update (simple): recompute avg rating for that segment+hour
    # Later you'll replace with your full multi-factor + trust + anomaly logic.
    stmt = select(Review.rating, Review.gender).where(
        Review.segment_id == payload.segment_id,
        Review.hour == payload.hour,
    )
    rows = db.execute(stmt).all()
    ratings = [float(x[0]) for x in rows]
    women_ratings = [float(x[0]) for x in rows if x[1] == "woman"]

    avg = sum(ratings) / len(ratings) if ratings else 0.5
    women_avg = (sum(women_ratings) / len(women_ratings)) if women_ratings else None

    # very basic anomaly rule for MVP
    anomaly = False
    if women_avg is not None and women_avg < 0.35 and avg > 0.7:
        anomaly = True
        avg = min(avg, 0.55)

    conf = min(1.0, 0.2 + 0.15 * len(ratings))  # grows with number of reviews

    # Upsert score row
    score_row = db.execute(
        select(Score).where(Score.segment_id == payload.segment_id, Score.hour == payload.hour)
    ).scalar_one_or_none()

    if score_row is None:
        score_row = Score(
            segment_id=payload.segment_id,
            hour=payload.hour,
            overall=avg,
            women=women_avg,
            confidence=conf,
            anomaly=anomaly,
        )
        db.add(score_row)
    else:
        score_row.overall = avg
        score_row.women = women_avg
        score_row.confidence = conf
        score_row.anomaly = anomaly

    db.commit()

    return {"status": "saved", "review_id": r.id}

@app.get("/scores/{segment_id}/{hour}")
def get_score(segment_id: str, hour: int, db: Session = Depends(get_db)):
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="hour must be 0..23")

    score = db.execute(
        select(Score).where(Score.segment_id == segment_id, Score.hour == hour)
    ).scalar_one_or_none()

    if score is None:
        return {"segment_id": segment_id, "hour": hour, "overall": 0.5, "women": None, "confidence": 0.2, "anomaly": False}

    return {
        "segment_id": score.segment_id,
        "hour": score.hour,
        "overall": float(score.overall),
        "women": (float(score.women) if score.women is not None else None),
        "confidence": float(score.confidence),
        "anomaly": bool(score.anomaly),
    }