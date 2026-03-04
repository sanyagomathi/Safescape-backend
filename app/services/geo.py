import math

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    # Earth radius (km)
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """
    Returns (min_lat, max_lat, min_lng, max_lng) approx bounding box.
    Good enough for MVP without PostGIS.
    """
    # 1 degree lat ~ 111 km
    lat_delta = radius_km / 111.0
    # 1 degree lng ~ 111 km * cos(lat)
    lng_delta = radius_km / (111.0 * max(0.2, math.cos(math.radians(lat))))
    return (lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta)