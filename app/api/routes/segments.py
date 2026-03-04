from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
import random
import math

from ...db import get_db
from ...models import Segment
from ...schemas.segment_schema import SegmentOut, SegmentSeedRequest
from ...services.geo import bounding_box, haversine_km

router = APIRouter(prefix="/segments", tags=["segments"])

@router.get("/nearby", response_model=list[SegmentOut])
def nearby_segments(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(1.0, ge=0.1, le=20.0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)

    segs = db.execute(
        select(Segment)
        .where(Segment.lat.between(min_lat, max_lat))
        .where(Segment.lng.between(min_lng, max_lng))
        .limit(limit)
    ).scalars().all()

    filtered = []
    for s in segs:
        d = haversine_km(lat, lng, float(s.lat), float(s.lng))
        if d <= radius_km:
            filtered.append(s)

    return filtered


def _meters_to_deg_lat(m: float) -> float:
    return m / 111_000.0

def _meters_to_deg_lng(m: float, lat: float) -> float:
    return m / (111_000.0 * max(0.2, math.cos(math.radians(lat))))


@router.post("/seed")
def seed_segments(payload: SegmentSeedRequest, db: Session = Depends(get_db)):
    """
    Hackathon/demo helper:
    Creates N segments around a center point (lat/lng).
    Safe to call multiple times: it will not overwrite existing IDs.
    """
    created = 0
    skipped = 0

    for i in range(payload.count):
        seg_id = f"{payload.id_prefix}{i+1:04d}"

        # skip if exists
        exists = db.execute(select(Segment).where(Segment.id == seg_id)).scalar_one_or_none()
        if exists is not None:
            skipped += 1
            continue

        # random point inside a circle (uniform-ish)
        r = payload.spread_m * math.sqrt(random.random())
        theta = 2 * math.pi * random.random()
        dx = r * math.cos(theta)
        dy = r * math.sin(theta)

        dlat = _meters_to_deg_lat(dy)
        dlng = _meters_to_deg_lng(dx, payload.center_lat)

        s = Segment(
            id=seg_id,
            lat=payload.center_lat + dlat,
            lng=payload.center_lng + dlng,
            lighting=payload.lighting,
            crowd=payload.crowd,
            shops_open=payload.shops_open,
            transport=payload.transport,
        )
        db.add(s)
        created += 1

    db.commit()
    return {
        "status": "ok",
        "created": created,
        "skipped_existing": skipped,
        "example_segment_id": f"{payload.id_prefix}0001",
    }