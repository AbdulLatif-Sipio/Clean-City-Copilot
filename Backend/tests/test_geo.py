import pytest
import math
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.geo import haversine_distance_meters, get_bounding_box, find_duplicate_ticket
from app.models import Complaint, Base


def test_haversine_identical_points():
    """Identical coordinates must yield exactly 0.0 meters."""
    dist = haversine_distance_meters(25.392000, 68.373500, 25.392000, 68.373500)
    assert dist == 0.0


def test_haversine_known_50m_distance():
    """
    Verify Haversine against two known coordinates in Hyderabad, Sindh (~50 meters apart).
    Point A: Pacco Qillo Shahi Bazaar (25.392000, 68.373500)
    Offset lat by ~0.0004499 degrees: (25.3924499, 68.373500)
    Expected distance: ~50.0 meters (within ±0.5m).
    """
    lat1, lon1 = 25.392000, 68.373500
    # 1 deg lat ≈ 111139 meters. 50m / 111139 ≈ 0.000449887
    lat2 = lat1 + (50.0 / 111139.0)
    lon2 = lon1

    distance = haversine_distance_meters(lat1, lon1, lat2, lon2)
    assert 49.5 <= distance <= 50.5, f"Expected ~50m, got {distance}m"


def test_haversine_boundary_thresholds_49m_vs_51m():
    """
    Explicit boundary testing in Hyderabad:
    - 49.0 meters -> strictly < 50.0
    - 49.9 meters -> strictly < 50.0
    - 50.1 meters -> strictly > 50.0
    - 51.0 meters -> strictly > 50.0
    """
    lat_center, lon_center = 25.392000, 68.373500
    deg_per_meter = 1.0 / 111139.0

    # 49.0m north
    lat_49m = lat_center + (49.0 * deg_per_meter)
    d_49m = haversine_distance_meters(lat_center, lon_center, lat_49m, lon_center)
    assert d_49m < 50.0
    assert abs(d_49m - 49.0) < 0.2

    # 49.9m north
    lat_49_9m = lat_center + (49.9 * deg_per_meter)
    d_49_9m = haversine_distance_meters(lat_center, lon_center, lat_49_9m, lon_center)
    assert d_49_9m < 50.0
    assert abs(d_49_9m - 49.9) < 0.2

    # 50.1m north
    lat_50_1m = lat_center + (50.1 * deg_per_meter)
    d_50_1m = haversine_distance_meters(lat_center, lon_center, lat_50_1m, lon_center)
    assert d_50_1m > 50.0
    assert abs(d_50_1m - 50.1) < 0.2

    # 51.0m north
    lat_51m = lat_center + (51.0 * deg_per_meter)
    d_51m = haversine_distance_meters(lat_center, lon_center, lat_51m, lon_center)
    assert d_51m > 50.0
    assert abs(d_51m - 51.0) < 0.2


def test_haversine_coordinate_validation():
    """Coordinates outside physical earth boundaries must raise ValueError."""
    with pytest.raises(ValueError):
        haversine_distance_meters(95.0, 67.0, 24.0, 67.0)

    with pytest.raises(ValueError):
        haversine_distance_meters(24.0, 190.0, 24.0, 67.0)


# ==============================================================================
# DATABASE SPATIAL-TEMPORAL DEDUPLICATION TESTS
# ==============================================================================
@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()


def test_geo_deduplication_scenarios(in_memory_db):
    """
    Comprehensive test of the geo-deduplication logic in Hyderabad, Sindh:
    1. Matching report at 30m distance -> Merged!
    2. Matching report at 49.5m distance -> Merged!
    3. Report at 51.5m distance -> NOT merged (New Ticket created).
    4. Report at 20m distance but DIFFERENT category (Pothole vs Garbage) -> NOT merged.
    5. Report at 20m distance but status is 'Resolved' -> NOT merged.
    6. Report at 20m distance but older than 48 hours -> NOT merged.
    """
    base_lat = 25.392000
    base_lon = 68.373500
    now = datetime.now(timezone.utc)
    deg_per_meter = 1.0 / 111139.0

    # 1. Seed an Open Garbage complaint in DB
    seed_ticket = Complaint(
        ticket_id="TKT-ORIG-01",
        image_path="media/images/seed.jpg",
        category="Garbage",
        severity="High",
        latitude=base_lat,
        longitude=base_lon,
        status="Open",
        is_valid_civic_issue=True,
        timestamp=now - timedelta(hours=2),
        duplicate_count=0
    )
    in_memory_db.add(seed_ticket)
    in_memory_db.commit()

    # Case A: Same category, 30m distance (inside 50m radius)
    lat_30m = base_lat + (30.0 * deg_per_meter)
    dup = find_duplicate_ticket(in_memory_db, category="Garbage", latitude=lat_30m, longitude=base_lon)
    assert dup is not None
    assert dup.ticket_id == "TKT-ORIG-01"

    # Case B: Same category, 49.5m distance (just inside 50m radius)
    lat_49_5m = base_lat + (49.5 * deg_per_meter)
    dup = find_duplicate_ticket(in_memory_db, category="Garbage", latitude=lat_49_5m, longitude=base_lon)
    assert dup is not None
    assert dup.ticket_id == "TKT-ORIG-01"

    # Case C: Same category, 51.5m distance (outside 50m radius -> What happens at 51 meters?)
    lat_51_5m = base_lat + (51.5 * deg_per_meter)
    dup = find_duplicate_ticket(in_memory_db, category="Garbage", latitude=lat_51_5m, longitude=base_lon)
    assert dup is None, "A report at 51.5 meters must NOT be merged (should create a new ticket)"

    # Case D: Same location (0m distance) but DIFFERENT category ("Pothole")
    dup_diff_cat = find_duplicate_ticket(in_memory_db, category="Pothole", latitude=base_lat, longitude=base_lon)
    assert dup_diff_cat is None, "Different categories at the same location must NOT be merged"

    # Case E: Same location, same category, but ticket is already 'Resolved'
    seed_ticket.status = "Resolved"
    in_memory_db.commit()
    dup_resolved = find_duplicate_ticket(in_memory_db, category="Garbage", latitude=base_lat, longitude=base_lon)
    assert dup_resolved is None, "Reports must NOT merge with already resolved tickets"

    # Case F: Ticket is 'Open' again, but timestamp is 50 hours old (> 48h limit)
    seed_ticket.status = "Open"
    seed_ticket.timestamp = now - timedelta(hours=50)
    in_memory_db.commit()
    dup_expired = find_duplicate_ticket(in_memory_db, category="Garbage", latitude=base_lat, longitude=base_lon)
    assert dup_expired is None, "Reports older than 48 hours must NOT be merged"
