from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Segment, Score, SafePoint
from .geo import bounding_box, haversine_km


def get_area_snapshot(
    db: Session,
    *,
    lat: float,
    lng: float,
    radius_km: float,
    hour: int | None = None,
) -> dict:
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)

    segments = db.execute(
        select(Segment)
        .where(Segment.lat.between(min_lat, max_lat))
        .where(Segment.lng.between(min_lng, max_lng))
    ).scalars().all()

    nearby_segments = []
    for s in segments:
        d = haversine_km(lat, lng, float(s.lat), float(s.lng))
        if d <= radius_km:
            nearby_segments.append(s)

    safe_points = db.execute(
        select(SafePoint)
        .where(SafePoint.lat.between(min_lat, max_lat))
        .where(SafePoint.lng.between(min_lng, max_lng))
    ).scalars().all()

    nearby_safe_points = []
    for p in safe_points:
        d = haversine_km(lat, lng, float(p.lat), float(p.lng))
        if d <= radius_km:
            nearby_safe_points.append(p)

    score_map = {}
    if hour is not None:
        for s in nearby_segments:
            score = db.execute(
                select(Score).where(Score.segment_id == s.id, Score.hour == hour)
            ).scalar_one_or_none()
            if score:
                score_map[s.id] = {
                    "overall": float(score.overall),
                    "confidence": float(score.confidence),
                    "anomaly": bool(score.anomaly),
                }

    avg_safety = 0.0
    low_safety_segments = 0
    anomaly_segments = 0

    if score_map:
        values = [v["overall"] for v in score_map.values()]
        avg_safety = sum(values) / len(values)
        low_safety_segments = sum(1 for v in score_map.values() if v["overall"] < 0.4)
        anomaly_segments = sum(1 for v in score_map.values() if v["anomaly"])
    else:
        # fallback from objective signals if scores are missing
        if nearby_segments:
            obj_vals = []
            for s in nearby_segments:
                val = (
                    0.30 * float(s.lighting)
                    + 0.25 * float(s.crowd)
                    + 0.25 * float(s.shops_open)
                    + 0.20 * float(s.transport)
                )
                obj_vals.append(val)
            avg_safety = sum(obj_vals) / len(obj_vals)
            low_safety_segments = sum(1 for v in obj_vals if v < 0.4)

    return {
        "segments_analyzed": len(nearby_segments),
        "avg_safety": round(avg_safety, 3),
        "low_safety_segments": low_safety_segments,
        "anomaly_segments": anomaly_segments,
        "safe_points_nearby": len(nearby_safe_points),
        "open_24x7_safe_points": sum(1 for p in nearby_safe_points if p.is_24x7),
        "police_points": sum(1 for p in nearby_safe_points if p.category == "police"),
        "medical_points": sum(1 for p in nearby_safe_points if p.category == "medical"),
        "transit_points": sum(1 for p in nearby_safe_points if p.category == "transit"),
        "commercial_points": sum(1 for p in nearby_safe_points if p.category == "commercial"),
    }