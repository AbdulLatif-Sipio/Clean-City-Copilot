import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Complaint

# Mean radius of the Earth in meters
EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula.

    :param lat1: Latitude of point 1 in decimal degrees (-90 to 90)
    :param lon1: Longitude of point 1 in decimal degrees (-180 to 180)
    :param lat2: Latitude of point 2 in decimal degrees (-90 to 90)
    :param lon2: Longitude of point 2 in decimal degrees (-180 to 180)
    :return: Distance in meters (float)
    """
    # Guard against out-of-range coordinates
    if not (-90.0 <= lat1 <= 90.0 and -90.0 <= lat2 <= 90.0):
        raise ValueError(f"Latitude must be between -90.0 and 90.0. Got lat1={lat1}, lat2={lat2}")
    if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
        raise ValueError(f"Longitude must be between -180.0 and 180.0. Got lon1={lon1}, lon2={lon2}")

    # Fast path for identical points
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    # Clamp 'a' to [0.0, 1.0] to prevent math domain error with floating precision
    a = min(1.0, max(0.0, a))
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_METERS * c


def get_bounding_box(lat: float, lon: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """
    Compute a conservative bounding box (min_lat, max_lat, min_lon, max_lon)
    for SQL spatial pre-filtering based on a search radius.

    1 deg latitude ≈ 111,139 meters
    1 deg longitude ≈ 111,139 * cos(lat) meters
    """
    lat_delta = radius_meters / 111139.0
    min_lat = max(-90.0, lat - lat_delta)
    max_lat = min(90.0, lat + lat_delta)

    # Near poles cosine approaches 0
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 1e-6:
        lon_delta = 180.0  # Search entire longitude span at the poles
    else:
        lon_delta = radius_meters / (111139.0 * cos_lat)

    min_lon = max(-180.0, lon - abs(lon_delta))
    max_lon = min(180.0, lon + abs(lon_delta))

    return min_lat, max_lat, min_lon, max_lon


def find_duplicate_ticket(
    db: Session,
    category: str,
    latitude: float,
    longitude: float,
    radius_meters: float = 50.0,
    time_window_hours: float = 48.0
) -> Optional[Complaint]:
    """
    Check if a similar complaint (same category, status='Open') exists within
    the specified radius (default 50m) in the last time_window_hours (default 48h).

    Uses a two-phase query:
    1. Fast SQL Bounding Box query using composite index (latitude, longitude, timestamp).
    2. Exact Haversine distance evaluation in Python on candidate rows.

    :return: The closest matching Complaint if within radius, else None.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

    # 1. Calculate bounding box for fast index scan
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius_meters)

    # 2. Query primary candidates from database (avoid centroid drift by matching root tickets)
    candidates = db.query(Complaint).filter(
        Complaint.status == "Open",
        Complaint.category == category,
        Complaint.duplicate_of.is_(None),
        Complaint.timestamp >= cutoff_time,
        Complaint.latitude >= min_lat,
        Complaint.latitude <= max_lat,
        Complaint.longitude >= min_lon,
        Complaint.longitude <= max_lon
    ).all()

    if not candidates:
        return None

    # 3. Evaluate exact Haversine distance and find the closest match
    closest_candidate: Optional[Complaint] = None
    min_distance = float("inf")

    for candidate in candidates:
        dist = haversine_distance_meters(
            latitude, longitude,
            candidate.latitude, candidate.longitude
        )
        if dist <= radius_meters and dist < min_distance:
            min_distance = dist
            closest_candidate = candidate

    return closest_candidate
