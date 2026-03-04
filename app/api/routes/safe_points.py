from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...db import get_db
from ...models import SafePoint
from ...schemas.safe_point_schema import SafePointOut
from ...services.geo import bounding_box, haversine_km

router = APIRouter(prefix="/safe-points", tags=["safe-points"])

@router.get("/nearby", response_model=list[SafePointOut])
def nearby_safe_points(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(2.0, ge=0.1, le=30.0),
    category: str | None = Query(None),  # police/medical/transit/commercial
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)

    q = (
        select(SafePoint)
        .where(SafePoint.lat.between(min_lat, max_lat))
        .where(SafePoint.lng.between(min_lng, max_lng))
    )
    if category:
        q = q.where(SafePoint.category == category)

    points = db.execute(q.limit(limit)).scalars().all()

    filtered = []
    for p in points:
        d = haversine_km(lat, lng, float(p.lat), float(p.lng))
        if d <= radius_km:
            filtered.append(p)

    return filtered