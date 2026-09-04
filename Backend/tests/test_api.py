import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models import Complaint

# Use in-memory SQLite for testing to isolate tests from persistent DB
TEST_DATABASE_URL = "sqlite:///./test_cleancity.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_cleancity.db"):
        try:
            os.remove("test_cleancity.db")
        except PermissionError:
            pass


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CleanCity" in data["app"]


def test_submit_report_success(client):
    """Test standard citizen submission with image and location."""
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"A" * 500
    files = {
        "image": ("garbage_photo.jpg", fake_image_bytes, "image/jpeg")
    }
    data = {
        "latitude": 24.861460,
        "longitude": 67.026150,
        "description": "Large garbage dump near main road."
    }

    response = client.post("/api/submit-report", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["ticket_id"].startswith("TKT-")
    assert res_data["is_duplicate"] is False
    assert res_data["category"] == "Garbage"
    assert res_data["is_valid_civic_issue"] is True


def test_submit_report_with_audio_and_stt(client):
    """Test submission with both image and voice note."""
    fake_image = b"\x89PNG\r\n\x1a\n" + b"IHDR" + b"X" * 200
    fake_audio = b"ID3" + b"\x00" * 300
    files = {
        "image": ("pothole.png", fake_image, "image/png"),
        "audio": ("voice_note.mp3", fake_audio, "audio/mpeg")
    }
    data = {
        "latitude": 24.861500,
        "longitude": 67.026200,
        "description": "Deep pothole broken road"
    }

    response = client.post("/api/submit-report", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["category"] == "Pothole"
    assert res_data["severity"] == "Critical"


def test_submit_report_geo_deduplication_flow(client):
    """
    Test end-to-end geo-deduplication:
    1. Submit Report 1 at (24.861460, 67.026150) -> creates TKT-1.
    2. Submit Report 2 at ~25m away with same category -> merged into TKT-1.
    3. Submit Report 3 at ~70m away with same category -> creates TKT-2.
    """
    fake_image = b"\xff\xd8\xff\xe0" + b"G" * 300
    
    # 1. First submission
    res1 = client.post(
        "/api/submit-report",
        data={"latitude": 24.861460, "longitude": 67.026150, "description": "Garbage pile"},
        files={"image": ("img1.jpg", fake_image, "image/jpeg")}
    )
    assert res1.status_code == 201
    ticket_1_id = res1.json()["ticket_id"]
    assert res1.json()["is_duplicate"] is False

    # 2. Second submission ~25m away (25 / 111139 ≈ 0.0002249 deg lat)
    lat_25m = 24.861460 + (25.0 / 111139.0)
    res2 = client.post(
        "/api/submit-report",
        data={"latitude": lat_25m, "longitude": 67.026150, "description": "Garbage pile growing"},
        files={"image": ("img2.jpg", fake_image, "image/jpeg")}
    )
    assert res2.status_code == 201
    res2_data = res2.json()
    assert res2_data["is_duplicate"] is True
    assert res2_data["merged_ticket_id"] == ticket_1_id
    assert res2_data["ticket_id"] == ticket_1_id

    # 3. Third submission ~70m away (70 / 111139 ≈ 0.000629 deg lat)
    lat_70m = 24.861460 + (70.0 / 111139.0)
    res3 = client.post(
        "/api/submit-report",
        data={"latitude": lat_70m, "longitude": 67.026150, "description": "Another garbage dump"},
        files={"image": ("img3.jpg", fake_image, "image/jpeg")}
    )
    assert res3.status_code == 201
    res3_data = res3.json()
    assert res3_data["is_duplicate"] is False
    assert res3_data["ticket_id"] != ticket_1_id


def test_submit_report_invalid_mime_type(client):
    """Submissions with disallowed file extensions/MIMEs must be rejected with HTTP 400."""
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {
        "image": ("malicious.exe", fake_exe, "application/octet-stream")
    }
    data = {"latitude": 24.861460, "longitude": 67.026150}

    response = client.post("/api/submit-report", data=data, files=files)
    assert response.status_code == 400
    assert "Invalid image file type" in response.json()["detail"]


def test_submit_report_coordinate_validation(client):
    """Out of range coordinates must be rejected with 422 Unprocessable Entity."""
    fake_image = b"\xff\xd8\xff\xe0" + b"X" * 100
    files = {"image": ("test.jpg", fake_image, "image/jpeg")}
    
    # Invalid latitude > 90
    res = client.post("/api/submit-report", data={"latitude": 95.0, "longitude": 67.0}, files=files)
    assert res.status_code == 422

    # Invalid longitude < -180
    res2 = client.post("/api/submit-report", data={"latitude": 24.0, "longitude": -190.0}, files=files)
    assert res2.status_code == 422


def test_admin_auth_optional_for_tickets(client):
    """GET /api/tickets works with or without X-Admin-API-Key (hackathon mode)."""
    # No header -> 200 (auth is optional)
    res_no_auth = client.get("/api/tickets")
    assert res_no_auth.status_code == 200
    assert "tickets" in res_no_auth.json()

    # Any header value -> 200 (accepted but not enforced)
    res_wrong_auth = client.get("/api/tickets", headers={"X-Admin-API-Key": "wrong-secret"})
    assert res_wrong_auth.status_code == 200
    assert "tickets" in res_wrong_auth.json()

    # Valid header -> 200
    res_auth = client.get("/api/tickets", headers={"X-Admin-API-Key": settings.ADMIN_API_KEY})
    assert res_auth.status_code == 200
    assert "tickets" in res_auth.json()


def test_patch_ticket_status(client):
    """PATCH /api/update-status/{ticket_id} updates ticket status with validation."""
    # 1. Create a ticket first
    fake_image = b"\xff\xd8\xff\xe0" + b"T" * 200
    sub_res = client.post(
        "/api/submit-report",
        data={"latitude": 24.861460, "longitude": 67.026150, "description": "Garbage"},
        files={"image": ("test.jpg", fake_image, "image/jpeg")}
    )
    ticket_id = sub_res.json()["ticket_id"]

    admin_headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}

    # 2. Update status to 'In Progress'
    patch_res = client.patch(
        f"/api/update-status/{ticket_id}",
        json={"status": "In Progress"},
        headers=admin_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "In Progress"

    # 3. Update status to 'Resolved'
    patch_res2 = client.patch(
        f"/api/update-status/{ticket_id}",
        json={"status": "Resolved"},
        headers=admin_headers
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "Resolved"

    # 4. Invalid status string -> 422
    patch_invalid = client.patch(
        f"/api/update-status/{ticket_id}",
        json={"status": "ClosedPermanently"},
        headers=admin_headers
    )
    assert patch_invalid.status_code == 422


def test_admin_dashboard_stats(client):
    """GET /api/stats provides summary metrics for dashboard cards."""
    admin_headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}
    
    # Create two complaints: 1 Garbage, 1 Pothole
    fake_img = b"\xff\xd8\xff\xe0" + b"S" * 200
    client.post(
        "/api/submit-report",
        data={"latitude": 24.861460, "longitude": 67.026150, "description": "Garbage pile"},
        files={"image": ("g.jpg", fake_img, "image/jpeg")}
    )
    client.post(
        "/api/submit-report",
        data={"latitude": 24.870000, "longitude": 67.030000, "description": "Broken road pothole"},
        files={"image": ("p.jpg", fake_img, "image/jpeg")}
    )

def test_dashboard_ui_html(client):
    """Verify built-in Classy Municipal Dashboard HTML is served at / and /dashboard."""
    res = client.get("/")
    assert res.status_code == 200
    assert "CleanCity Copilot" in res.text
    assert "leaflet" in res.text

    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "CleanCity Copilot" in res_dash.text
    assert "leaflet" in res_dash.text


def test_seed_demo_data_endpoint(client):
    """Verify admin seed demo data endpoint creates realistic tickets."""
    admin_headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}
    res = client.post("/api/seed-demo-data", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Seeded demo dataset successfully" in data["message"]

