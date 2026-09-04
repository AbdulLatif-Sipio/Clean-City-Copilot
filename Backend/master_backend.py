"""
========================================================================================
🚀 Master Standalone Backend: CleanCity Copilot
Target: Alibaba Cloud AI Hackathon 2026
----------------------------------------------------------------------------------------
This single-file master script contains the ENTIRE backend, database layer, 
geo-deduplication engine, security hardening, AI integration stubs, and the 
built-in 3D Cyberpunk Web Dashboard.

Run with:
    python master_backend.py
or:
    uvicorn master_backend:app --reload --host 0.0.0.0 --port 8000
========================================================================================
"""

import os
import io
import math
import uuid
import secrets
import logging
from typing import Generator, List, Optional, Dict, Any, Set, Tuple, Union
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from enum import Enum

# Third-party imports
from fastapi import FastAPI, Request, Depends, Form, File, UploadFile, HTTPException, Query, Security, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy import create_engine, event, Column, String, Float, Text, Boolean, DateTime, Integer, Index, func, desc
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ======================================================================================
# 1. CONFIGURATION & SETTINGS
# ======================================================================================
class Settings(BaseSettings):
    APP_NAME: str = "CleanCity Copilot API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./cleancity.db"

    # Security
    ADMIN_API_KEY: str = "cleancity-admin-secret-key-2026"

    # Rate Limiting & Storage
    SUBMIT_RATE_LIMIT: str = "30/minute"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "media"
    IMAGE_SUBDIR: str = "media/images"
    AUDIO_SUBDIR: str = "media/audio"

    # Geo-Deduplication Parameters
    GEO_DEDUP_RADIUS_METERS: float = 50.0
    GEO_DEDUP_TIME_WINDOW_HOURS: float = 48.0

    # CORS Whitelist
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000"

    # AI Pipeline
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

settings = Settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cleancity")


# ======================================================================================
# 2. DATABASE & ORM MODELS (SQLAlchemy 2.0 + SQLite)
# ======================================================================================
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_ticket_id() -> str:
    """Generate human-friendly ticket ID: e.g. TKT-A8F12C."""
    return f"TKT-{uuid.uuid4().hex[:6].upper()}"


class Complaint(Base):
    """
    Core SQLAlchemy ORM model representing civic complaints.
    """
    __tablename__ = "complaints"

    ticket_id = Column(String(32), primary_key=True, index=True, default=generate_ticket_id)
    image_path = Column(String(512), nullable=False)
    original_audio_path = Column(String(512), nullable=True)
    translated_text = Column(Text, nullable=True)
    category = Column(String(32), nullable=False, default="Unassigned", index=True)
    severity = Column(String(16), nullable=False, default="Medium", index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    ai_action_plan = Column(Text, nullable=True)
    is_valid_civic_issue = Column(Boolean, nullable=False, default=True, index=True)
    status = Column(String(16), nullable=False, default="Open", index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    duplicate_of = Column(String(32), nullable=True)
    duplicate_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Composite index for high-speed spatial-temporal geo-deduplication
        Index("ix_complaints_geo_time", "latitude", "longitude", "timestamp"),
        # Composite index for fast admin dashboard filtering
        Index("ix_complaints_admin_filter", "status", "category", "is_valid_civic_issue"),
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_upload_dirs() -> None:
    os.makedirs(settings.IMAGE_SUBDIR, exist_ok=True)
    os.makedirs(settings.AUDIO_SUBDIR, exist_ok=True)


# ======================================================================================
# 3. PYDANTIC SCHEMAS & ENUMS
# ======================================================================================
class CategoryEnum(str, Enum):
    GARBAGE = "Garbage"
    POTHOLE = "Pothole"
    SEWERAGE = "Sewerage"
    UNASSIGNED = "Unassigned"


class SeverityEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class StatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    image_path: str
    original_audio_path: Optional[str] = None
    translated_text: Optional[str] = None
    category: str
    severity: str
    latitude: float
    longitude: float
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    ai_action_plan: Optional[str] = None
    is_valid_civic_issue: bool
    status: str
    timestamp: datetime
    created_at: Optional[str] = None
    duplicate_of: Optional[str] = None
    duplicate_count: int = 0


class TicketListResponse(BaseModel):
    total: int
    count: int
    limit: int
    offset: int
    tickets: List[TicketResponse]


class TicketStatusUpdate(BaseModel):
    status: StatusEnum

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        if isinstance(value, str):
            val_norm = value.strip().title()
            if val_norm == "In-Progress":
                return "In Progress"
            return val_norm
        return value


class ReportSubmissionResponse(BaseModel):
    success: bool = True
    status: str
    ticket_id: str
    is_duplicate: bool
    merged_ticket_id: Optional[str] = None
    category: str
    severity: str
    is_valid_civic_issue: bool
    ai_action_plan: Optional[str] = None
    translated_text: Optional[str] = None
    message: str


class AdminDashboardStats(BaseModel):
    total_open: int
    critical_alerts: int
    resolved_today: int
    total_reports: int
    category_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]


# ======================================================================================
# 4. SECURITY & AUTHENTICATION (X-Admin-API-Key) — Hackathon mode: key optional
# ======================================================================================
API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def verify_admin_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Zero-friction Hackathon mode: API key requirement is removed!
    Allows seamless, direct testing in Swagger (/docs), Streamlit frontend,
    and Postman without getting 401 errors.
    """
    if api_key_header:
        return api_key_header
    return "authorized-admin"


# ======================================================================================
# 5. GEO-DEDUPLICATION ENGINE (Haversine 50m / 48hr Window)
# ======================================================================================
EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two GPS coordinates."""
    if not (-90.0 <= lat1 <= 90.0 and -90.0 <= lat2 <= 90.0):
        raise ValueError("Latitude must be between -90.0 and 90.0.")
    if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
        raise ValueError("Longitude must be between -180.0 and 180.0.")

    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def get_bounding_box(lat: float, lon: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """Calculate SQL bounding box for index scanning."""
    lat_delta = radius_meters / 111139.0
    min_lat = max(-90.0, lat - lat_delta)
    max_lat = min(90.0, lat + lat_delta)

    cos_lat = math.cos(math.radians(lat))
    lon_delta = 180.0 if abs(cos_lat) < 1e-6 else radius_meters / (111139.0 * cos_lat)
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
    """Finds existing open ticket within radius and time window, anchored to primary tickets."""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius_meters)

    candidates = db.query(Complaint).filter(
        Complaint.status == "Open",
        Complaint.category == category,
        Complaint.duplicate_of.is_(None),  # Anchor to root tickets to prevent centroid drift
        Complaint.timestamp >= cutoff_time,
        Complaint.latitude >= min_lat,
        Complaint.latitude <= max_lat,
        Complaint.longitude >= min_lon,
        Complaint.longitude <= max_lon
    ).all()

    if not candidates:
        return None

    closest_candidate: Optional[Complaint] = None
    min_dist = float("inf")
    for cand in candidates:
        dist = haversine_distance_meters(latitude, longitude, cand.latitude, cand.longitude)
        if dist <= radius_meters and dist < min_dist:
            min_dist = dist
            closest_candidate = cand

    return closest_candidate


# ======================================================================================
# 6. AI PIPELINE INTEGRATION STUBS & HEURISTICS (Whisper + Vision LLM)
# ======================================================================================
class AIAnalysisResult(BaseModel):
    is_valid_civic_issue: bool
    category: str
    severity: str
    reasoning: str
    ai_action_plan: str
    translated_text: Optional[str] = None
    raw_ai_response: Optional[Dict[str, Any]] = None


def transcribe_and_translate_audio(audio_path: Optional[str]) -> Optional[str]:
    """Integration stub for Whisper Speech-to-Text translation (Urdu/Roman Urdu -> English)."""
    if not audio_path or not os.path.exists(audio_path):
        return None
    
    path_lower = audio_path.lower()
    if "pothole" in path_lower or "sarak" in path_lower or "road" in path_lower:
        return "Deep pothole on broken road causing hazard."
    elif "sewer" in path_lower or "gatar" in path_lower or "drain" in path_lower:
        return "Sewerage water overflowing from blocked drain."
    elif "garbage" in path_lower or "kachra" in path_lower:
        return "Reported overflowing garbage pile near the street corner requiring cleanup."

    return "Voice report describing civic issue requiring municipal cleanup."


def analyze_civic_issue(
    image_path: str,
    translated_text: Optional[str] = None,
    user_description: Optional[str] = None
) -> AIAnalysisResult:
    """Multimodal Vision & Logic Classification with strict JSON schema."""
    combined_context = f"{translated_text or ''} {user_description or ''}".strip().lower()

    # Dynamic classification heuristic with mock fallback
    if "selfie" in combined_context or "blank" in combined_context or "fake" in combined_context or "spam" in combined_context:
        return AIAnalysisResult(
            is_valid_civic_issue=False,
            category="Unassigned",
            severity="Low",
            reasoning="Image flagged as unrelated to municipal civic infrastructure.",
            ai_action_plan="No municipal action required.",
            translated_text=translated_text or user_description
        )
    elif any(k in combined_context for k in ["garbage", "kachra", "trash", "waste", "dump", "debris", "litter"]):
        return AIAnalysisResult(
            is_valid_civic_issue=True,
            category="Garbage",
            severity="Critical" if any(k in combined_context for k in ["huge", "massive", "blocking", "severe"]) else "High",
            reasoning="Accumulated solid waste obstructing public area.",
            ai_action_plan="Requires 1 dump truck and 3 sanitation workers for 2 hours.",
            translated_text=translated_text or user_description
        )
    elif any(k in combined_context for k in ["pothole", "gaddha", "crater", "tooti hui", "tooti sarak", "broken road", "damaged road"]):
        return AIAnalysisResult(
            is_valid_civic_issue=True,
            category="Pothole",
            severity="Critical" if any(k in combined_context for k in ["deep", "huge", "dangerous", "severe", "broken"]) else "High",
            reasoning="Severe road fracture posing danger to traffic.",
            ai_action_plan="Requires 1 asphalt patcher truck and 2 road repair technicians.",
            translated_text=translated_text or user_description
        )
    elif any(k in combined_context for k in ["sewer", "gatar", "gutter", "drain", "sewage", "sewerage", "naali", "manhole", "ganda paani"]):
        return AIAnalysisResult(
            is_valid_civic_issue=True,
            category="Sewerage",
            severity="Critical",
            reasoning="Blocked sewerage line with contaminated water overflow.",
            ai_action_plan="Requires 1 suction jetting machine truck and 2 drainage specialists.",
            translated_text=translated_text or user_description
        )
    else:
        return AIAnalysisResult(
            is_valid_civic_issue=True,
            category="Garbage",
            severity="Medium",
            reasoning="Civic cleanliness concern reported in public area.",
            ai_action_plan="Requires sanitation inspection and standard clearance team.",
            translated_text=translated_text or user_description
        )


def process_civic_submission(
    image_path: str,
    audio_path: Optional[str] = None,
    user_description: Optional[str] = None
) -> AIAnalysisResult:
    translated_audio_text = transcribe_and_translate_audio(audio_path) if audio_path else None
    final_text = translated_audio_text or user_description
    res = analyze_civic_issue(image_path=image_path, translated_text=final_text, user_description=user_description)
    if translated_audio_text and not res.translated_text:
        res.translated_text = translated_audio_text
    return res


# ======================================================================================
# 7. SECURE FILE UPLOAD HANDLER
# ======================================================================================
ALLOWED_IMAGE_TYPES: Set[str] = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES: Set[str] = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "audio/mp4", "audio/webm"}

MIME_EXT_MAP = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg", "audio/m4a": ".m4a"
}


async def save_uploaded_file(file: UploadFile, is_image: bool = True) -> str:
    """Validates MIME, checks size stream up to 10MB, and saves with UUID filename."""
    ensure_upload_dirs()
    content_type = (file.content_type or "").lower().strip()
    allowed = ALLOWED_IMAGE_TYPES if is_image else ALLOWED_AUDIO_TYPES
    target_dir = settings.IMAGE_SUBDIR if is_image else settings.AUDIO_SUBDIR

    if content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid file type '{content_type}'. Allowed: {sorted(list(allowed))}")

    ext = MIME_EXT_MAP.get(content_type, ".jpg" if is_image else ".mp3")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(target_dir, unique_name)

    total_bytes = 0
    try:
        with open(dest_path, "wb") as buffer:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(status_code=413, detail=f"File exceeds max 10MB limit.")
                buffer.write(chunk)
    finally:
        await file.seek(0)

    return dest_path.replace("\\", "/")


# ======================================================================================
# 8. HYDERABAD SINDH DEMO DATA SEEDING UTILITY
# ======================================================================================
HYDERABAD_DEMO_COMPLAINTS = [
    {
        "category": "Garbage", "severity": "Critical", "latitude": 25.392000, "longitude": 68.373500,
        "description": "Pacco Qillo Shahi Bazaar gate solid waste accumulation blocking road.",
        "translated_text": "Massive solid waste accumulation blocking main entrance of Pacco Qillo near Shahi Bazaar.",
        "ai_action_plan": "Deploy 2 heavy dumpers, 1 mini-loader excavator, and 6 sanitation workers for 3 hours.",
        "status": "Open", "duplicate_count": 5
    },
    {
        "category": "Pothole", "severity": "Critical", "latitude": 25.378000, "longitude": 68.352000,
        "description": "Autobahn road Latifabad Unit 2 deep pothole crater.",
        "translated_text": "Deep hazardous pothole on Autobahn Road Latifabad posing danger to two-wheelers and vehicles.",
        "ai_action_plan": "Deploy 1 rapid asphalt cold-mix repair truck and 2 highway patch technicians.",
        "status": "Open", "duplicate_count": 4
    },
    {
        "category": "Sewerage", "severity": "Critical", "latitude": 25.395000, "longitude": 68.332000,
        "description": "Qasimabad Naseem Nagar chowk sewerage overflow submerging shops.",
        "translated_text": "Severe sewerage overflow at Naseem Nagar Chowk Qasimabad submerging commercial shops in wastewater.",
        "ai_action_plan": "Deploy 2 high-capacity suction jetting tankers and 4 WASA drainage technicians.",
        "status": "Open", "duplicate_count": 6
    },
    {
        "category": "Garbage", "severity": "High", "latitude": 25.367000, "longitude": 68.358000,
        "description": "Latifabad Unit 7 General Hospital walkway refuse accumulation.",
        "translated_text": "Commercial refuse accumulation near Latifabad Unit 7 General Hospital walkway.",
        "ai_action_plan": "Deploy 1 compact compactor truck and 3 municipal sanitation workers.",
        "status": "In Progress", "duplicate_count": 2
    },
    {
        "category": "Pothole", "severity": "High", "latitude": 25.405000, "longitude": 68.338000,
        "description": "Wadhu Wah road road surface fractures.",
        "translated_text": "Extensive road surface fractures and loose gravel on Wadhu Wah Road Qasimabad.",
        "ai_action_plan": "Schedule asphalt leveling crew and road rolling machinery.",
        "status": "In Progress", "duplicate_count": 2
    },
    {
        "category": "Sewerage", "severity": "Medium", "latitude": 25.391000, "longitude": 68.362000,
        "description": "Haider Chowk Saddar storm drain blockage.",
        "translated_text": "Storm drain blockage near Haider Chowk Saddar causing stagnant street water.",
        "ai_action_plan": "Deploy manual drain rodding team to clear obstruction.",
        "status": "Resolved", "duplicate_count": 1
    },
    {
        "category": "Garbage", "severity": "High", "latitude": 25.397000, "longitude": 68.369000,
        "description": "Station Road / Resham Gali market packaging refuse.",
        "translated_text": "Market packing refuse and debris along Station Road market avenue.",
        "ai_action_plan": "Deploy night-shift mechanical sweeper and waste truck.",
        "status": "Open", "duplicate_count": 3
    },
    {
        "category": "Pothole", "severity": "Critical", "latitude": 25.432000, "longitude": 68.315000,
        "description": "Kotri Barrage Indus Bridge approach structural potholes.",
        "translated_text": "Multiple deep structural potholes on Kotri Barrage approach road damaging freight trucks.",
        "ai_action_plan": "Emergency road patching crew with heavy asphalt paver.",
        "status": "Open", "duplicate_count": 7
    },
    {
        "category": "Garbage", "severity": "Medium", "latitude": 25.402000, "longitude": 68.356000,
        "description": "Thandi Sarak / Hyderabad Gymkhana green median debris.",
        "translated_text": "Organic refuse and pruning debris left on Thandi Sarak median.",
        "ai_action_plan": "Deploy horticultural waste collection vehicle.",
        "status": "Resolved", "duplicate_count": 0
    },
    {
        "category": "Pothole", "severity": "High", "latitude": 25.394000, "longitude": 68.365000,
        "description": "Hirabad Tower Market roundabout damaged surface.",
        "translated_text": "Fractured road asphalt around Hirabad Tower Market roundabout.",
        "ai_action_plan": "Apply cold-patch asphalt filler and compact surface.",
        "status": "Open", "duplicate_count": 2
    },
    {
        "category": "Sewerage", "severity": "High", "latitude": 25.388000, "longitude": 68.341000,
        "description": "Citizen Colony residential sewer backflow.",
        "translated_text": "Residential sewer line backflow causing street flooding in Citizen Colony.",
        "ai_action_plan": "Deploy municipal jetting tanker to flush pipeline blockage.",
        "status": "Open", "duplicate_count": 3
    },
    {
        "category": "Garbage", "severity": "Critical", "latitude": 25.385000, "longitude": 68.318000,
        "description": "SITE Industrial Area solid waste dump.",
        "translated_text": "Illegal industrial solid waste dump blocking primary access lane in SITE Hyderabad.",
        "ai_action_plan": "Dispatch heavy wheel-loader and two 20-ton dumper trucks with inspector.",
        "status": "In Progress", "duplicate_count": 4
    }
]


def seed_demo_data(db: Session = None, force_reset: bool = False) -> int:
    ensure_upload_dirs()
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        if force_reset:
            db.query(Complaint).delete()
            db.commit()
        elif db.query(Complaint).count() >= len(HYDERABAD_DEMO_COMPLAINTS):
            return db.query(Complaint).count()

        sample_img = "media/images/hyderabad_demo_sample.jpg"
        if not os.path.exists(sample_img):
            with open(sample_img, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 400)

        now = datetime.now(timezone.utc)
        for i, item in enumerate(HYDERABAD_DEMO_COMPLAINTS):
            c = Complaint(
                ticket_id=f"HYD-TKT-10{i+1:02d}",
                image_path=sample_img,
                translated_text=item["translated_text"],
                category=item["category"],
                severity=item["severity"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                ai_action_plan=item["ai_action_plan"],
                is_valid_civic_issue=True,
                status=item["status"],
                timestamp=now - timedelta(hours=3 * (i + 1)),
                duplicate_count=item["duplicate_count"]
            )
            db.add(c)
        db.commit()
        return len(HYDERABAD_DEMO_COMPLAINTS)
    finally:
        if close_db:
            db.close()


# ======================================================================================
# 9. BUILT-IN CLASSY NATURAL MUNICIPAL DASHBOARD WITH REAL HYDERABAD MAP
# ======================================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CleanCity Copilot | Municipal Triage Engine (Hyderabad, Sindh)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --bg-page: #f8fafc; --surface: #ffffff; --surface-muted: #f1f5f9;
            --border: #e2e8f0; --border-strong: #cbd5e1; --text-main: #0f172a; --text-muted: #64748b;
            --civic-blue: #1e40af; --civic-blue-hover: #1d4ed8;
            --crit-bg: #fef2f2; --crit-text: #b91c1c; --crit-border: #fecaca;
            --high-bg: #fffbeb; --high-text: #b45309; --high-border: #fde68a;
            --med-bg: #eff6ff; --med-text: #1d4ed8; --med-border: #bfdbfe;
            --res-bg: #ecfdf5; --res-text: #047857; --res-border: #a7f3d0;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background: var(--bg-page); color: var(--text-main); font-family: 'Inter', sans-serif; padding: 1.5rem 2rem; }
        .top-navbar { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.75rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 1.5rem; }
        .brand-box { display: flex; align-items: center; gap: 14px; }
        .gov-seal { width: 44px; height: 44px; background: #eff6ff; border: 1px solid #bfdbfe; color: var(--civic-blue); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
        .brand-title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.35rem; font-weight: 800; color: var(--text-main); }
        .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
        .kpi-title { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }
        .kpi-value { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.85rem; font-weight: 800; color: var(--text-main); margin: 0.35rem 0; }
        .tab-bar { display: flex; gap: 8px; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
        .tab-btn { background: none; border: none; border-bottom: 2px solid transparent; padding: 0.75rem 1.25rem; font-size: 0.95rem; font-weight: 600; color: var(--text-muted); cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
        .tab-btn.active { color: var(--civic-blue); border-bottom-color: var(--civic-blue); }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }
        .map-section, .db-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
        #real-map { width: 100%; height: 500px; border-radius: 10px; border: 1px solid var(--border); }
        .db-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 1rem; }
        .db-table th { background: var(--surface-muted); color: var(--text-main); font-weight: 600; text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
        .db-table td { padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); color: #475569; }
        .badge { display: inline-flex; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-Critical { background: var(--crit-bg); color: var(--crit-text); border: 1px solid var(--crit-border); }
        .badge-High { background: var(--high-bg); color: var(--high-text); border: 1px solid var(--high-border); }
        .badge-Medium { background: var(--med-bg); color: var(--med-text); border: 1px solid var(--med-border); }
        .btn-action { display: inline-flex; align-items: center; gap: 8px; padding: 0.55rem 1rem; font-size: 0.88rem; font-weight: 600; border-radius: 8px; cursor: pointer; text-decoration: none; }
        .btn-outline { background: var(--surface); border: 1px solid var(--border-strong); color: #475569; }
        .btn-primary { background: var(--civic-blue); border: 1px solid var(--civic-blue); color: #fff; }
    </style>
</head>
<body>
    <header class="top-navbar">
        <div class="brand-box">
            <div class="gov-seal"><i class="fa-solid fa-landmark"></i></div>
            <div>
                <h1 class="brand-title">CleanCity Copilot</h1>
                <div style="font-size:0.85rem; color:var(--text-muted);">Municipal Triage &bull; <span style="background:#f1f5f9; padding:2px 8px; border-radius:6px; font-weight:600;">Hyderabad, Sindh</span></div>
            </div>
        </div>
        <div style="display:flex; gap:10px;">
            <button class="btn-action btn-outline" onclick="seedHyderabadData()"><i class="fa-solid fa-database"></i> Seed Hyderabad Data</button>
            <a href="http://localhost:8501" target="_blank" class="btn-action btn-outline"><i class="fa-solid fa-desktop"></i> Open Streamlit Frontend</a>
            <a href="/docs" target="_blank" class="btn-action btn-primary"><i class="fa-solid fa-code"></i> API Docs</a>
        </div>
    </header>

    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">Active Open Issues</div><div class="kpi-value" id="kpi-open">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Critical Road/Drain Hazards</div><div class="kpi-value" style="color:var(--crit-text);" id="kpi-crit">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Resolved Today</div><div class="kpi-value" style="color:var(--res-text);" id="kpi-res">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Total Verified Reports</div><div class="kpi-value" id="kpi-total">--</div></div>
    </div>

    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-map')"><i class="fa-solid fa-map-location-dot"></i> Real Hyderabad Street Map & 50m Deduplication</button>
        <button class="tab-btn" onclick="switchTab('tab-db')"><i class="fa-solid fa-table-list"></i> Municipal Admin Database Explorer</button>
        <button class="tab-btn" onclick="switchTab('tab-submit')"><i class="fa-solid fa-paper-plane"></i> Citizen Issue Submission & AI Triage</button>
    </div>

    <div id="tab-map" class="tab-pane active">
        <div class="map-section">
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                <div><h3 style="font-size:1.1rem; font-weight:700;">Real Geographic Map &bull; Hyderabad, Sindh</h3><small style="color:var(--text-muted);">Real street-level coordinates with 50-meter deduplication perimeters.</small></div>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-rotate"></i> Refresh Map</button>
            </div>
            <div id="real-map"></div>
        </div>
    </div>

    <div id="tab-db" class="tab-pane">
        <div class="db-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                <h3 style="font-size:1.1rem; font-weight:700;">SQLite Database Explorer (`complaints` Table)</h3>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-rotate"></i> Refresh Table</button>
            </div>
            <div style="overflow-x:auto;">
                <table class="db-table">
                    <thead><tr><th>Ticket ID</th><th>Category</th><th>Severity</th><th>Landmark / GPS</th><th>AI Action Plan</th><th>Duplicates</th><th>Status (Click to Update)</th></tr></thead>
                    <tbody id="db-tbody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <div id="tab-submit" class="tab-pane">
        <div class="db-card">
            <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:1rem;">Citizen Complaint Submission</h3>
            <form id="report-form" style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">
                <div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Issue Photo (JPEG, PNG, WebP)</label><input type="file" id="form-image" accept="image/*" required style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Voice Note in Urdu / Sindhi (Optional)</label><input type="file" id="form-audio" accept="audio/*" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Description</label><input type="text" id="form-desc" placeholder="e.g. Autobahn road Latifabad main deep pothole hai" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                </div>
                <div>
                    <div style="margin-bottom:1rem;">
                        <label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Hyderabad Landmark Presets</label>
                        <select id="landmark-select" onchange="const p=this.value.split(','); document.getElementById('form-lat').value=p[0]; document.getElementById('form-lon').value=p[1];" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;">
                            <option value="25.392000,68.373500">Pacco Qillo (Pakka Qila), Shahi Bazaar Gate</option>
                            <option value="25.378000,68.352000">Autobahn Road, Latifabad Unit 2</option>
                            <option value="25.395000,68.332000">Naseem Nagar Chowk, Qasimabad</option>
                            <option value="25.367000,68.358000">Latifabad Unit 7, Near General Hospital</option>
                            <option value="25.405000,68.338000">Wadhu Wah Road, Qasimabad</option>
                            <option value="25.432000,68.315000">Kotri Barrage Indus Bridge Approach</option>
                        </select>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:1rem;">
                        <div><label style="display:block; font-size:0.85rem; font-weight:600;">Latitude</label><input type="text" id="form-lat" value="25.392000" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                        <div><label style="display:block; font-size:0.85rem; font-weight:600;">Longitude</label><input type="text" id="form-lon" value="68.373500" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    </div>
                    <button type="submit" class="btn-action btn-primary" id="btn-sub" style="width:100%; justify-content:center; padding:10px;"><i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline</button>
                </div>
            </form>
            <div id="ai-resp-card" style="display:none; margin-top:1.5rem; padding:1.25rem; background:#f1f5f9; border-radius:10px;">
                <h4 style="color:var(--civic-blue);" id="resp-tkt"></h4>
                <div id="resp-meta" style="margin:6px 0;"></div>
                <div id="resp-dedup" style="color:#b45309; font-weight:600;"></div>
                <p style="margin-top:6px;"><b>AI Action Plan:</b> <span id="resp-plan"></span></p>
            </div>
        </div>
    </div>

    <script>
        const ADMIN_KEY = "cleancity-admin-secret-key-2026";
        let map, markersLayer, circlesLayer;
        const HYD_LAT = 25.392000, HYD_LON = 68.362000;

        function initMap() {
            map = L.map('real-map').setView([HYD_LAT, HYD_LON], 13);
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
            markersLayer = L.layerGroup().addTo(map);
            circlesLayer = L.layerGroup().addTo(map);
        }

        function switchTab(id) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.currentTarget.classList.add('active');
            if (id === 'tab-map' && map) setTimeout(() => map.invalidateSize(), 150);
        }

        async function loadDashboardData() {
            try {
                const s = await (await fetch('/api/stats', { headers: {'X-Admin-API-Key': ADMIN_KEY} })).json();
                document.getElementById('kpi-open').innerText = s.total_open;
                document.getElementById('kpi-crit').innerText = s.critical_alerts;
                document.getElementById('kpi-res').innerText = s.resolved_today;
                document.getElementById('kpi-total').innerText = s.total_reports;

                const resp = await (await fetch('/api/tickets?limit=100', { headers: {'X-Admin-API-Key': ADMIN_KEY} })).json();
                const tickets = resp.tickets || resp || [];

                markersLayer.clearLayers(); circlesLayer.clearLayers();
                tickets.forEach(t => {
                    const col = t.severity === 'Critical' ? '#dc2626' : (t.severity === 'High' ? '#d97706' : '#2563eb');
                    L.circle([t.latitude, t.longitude], { radius: 50, color: col, fillColor: col, fillOpacity: 0.12, dashArray: '4, 4' }).addTo(circlesLayer);
                    L.circleMarker([t.latitude, t.longitude], { radius: 8, fillColor: col, color: '#fff', weight: 2, fillOpacity: 0.95 }).addTo(markersLayer)
                        .bindPopup(`<b>${t.ticket_id} [${t.category}]</b><br>Severity: ${t.severity}<br>Action: ${t.ai_action_plan}`);
                });

                const tb = document.getElementById('db-tbody'); tb.innerHTML = '';
                tickets.forEach(t => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td style="font-weight:700; color:var(--civic-blue);">${t.ticket_id}</td>
                    <td><b>${t.category}</b></td>
                    <td><span class="badge badge-${t.severity}">${t.severity}</span></td>
                    <td style="font-size:0.82rem;">${t.translated_text || 'Hyderabad'}<br><span style="font-family:monospace; color:var(--text-muted);">${t.latitude.toFixed(4)}, ${t.longitude.toFixed(4)}</span></td>
                    <td style="font-size:0.82rem;">${t.ai_action_plan}</td>
                    <td><span style="font-weight:600; color:var(--civic-blue);">${t.duplicate_count} merged</span></td>
                    <td><select onchange="updateTicketStatus('${t.ticket_id}', this.value)" style="padding:4px 8px; border-radius:6px;">
                        <option value="Open" ${t.status==='Open'?'selected':''}>Open</option>
                        <option value="In Progress" ${t.status==='In Progress'?'selected':''}>In Progress</option>
                        <option value="Resolved" ${t.status==='Resolved'?'selected':''}>Resolved</option>
                    </select></td>`;
                    tb.appendChild(tr);
                });
            } catch(e) { console.error(e); }
        }

        async function updateTicketStatus(id, stat) {
            await fetch(`/api/update-status/${id}`, { method:'PATCH', headers:{'Content-Type':'application/json', 'X-Admin-API-Key':ADMIN_KEY}, body:JSON.stringify({status:stat}) });
            loadDashboardData();
        }

        async function seedHyderabadData() {
            const r = await (await fetch('/api/seed-demo-data', { method:'POST', headers:{'X-Admin-API-Key':ADMIN_KEY} })).json();
            alert(r.message); loadDashboardData();
        }

        document.getElementById('report-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-sub');
            btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
            const fd = new FormData();
            fd.append('image', document.getElementById('form-image').files[0]);
            if (document.getElementById('form-audio').files[0]) fd.append('audio', document.getElementById('form-audio').files[0]);
            fd.append('latitude', document.getElementById('form-lat').value);
            fd.append('longitude', document.getElementById('form-lon').value);
            fd.append('description', document.getElementById('form-desc').value);

            const res = await (await fetch('/api/submit-report', { method:'POST', body:fd })).json();
            document.getElementById('ai-resp-card').style.display = 'block';
            document.getElementById('resp-tkt').innerText = `Ticket ID: ${res.ticket_id}`;
            document.getElementById('resp-meta').innerHTML = `<b>Category:</b> ${res.category} &bull; <b>Severity:</b> <span class="badge badge-${res.severity}">${res.severity}</span>`;
            document.getElementById('resp-dedup').innerText = res.is_duplicate ? '🔄 Merged within 50m radius' : '🆕 New verified issue registered';
            document.getElementById('resp-plan').innerText = res.ai_action_plan;
            btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline';
            loadDashboardData();
        };

        window.onload = () => { initMap(); loadDashboardData(); };
    </script>
</body>
</html>
"""


# ======================================================================================
# 10. FASTAPI APPLICATION INITIALIZATION & ROUTING
# ======================================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CleanCity Copilot Master Backend...")
    ensure_upload_dirs()
    init_db()
    seed_demo_data()
    logger.info("Database and media storage directories initialized successfully.")
    yield
    logger.info("CleanCity Copilot Master Backend shutting down.")


app = FastAPI(
    title="🏙️ " + settings.APP_NAME,
    version="1.0.0",
    description="Unified Master Backend & 3D Geospatial Engine for CleanCity Copilot (Alibaba Cloud AI Hackathon 2026).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError, RateLimitExceeded)):
        raise exc
    logger.error(f"Server error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error occurred."})


# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard UI"])
async def dashboard_view():
    """Serves the built-in 3D Cyberpunk Dashboard."""
    return DASHBOARD_HTML


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0", "environment": settings.APP_ENV}


HYDERABAD_LANDMARKS = {
    "pacco qillo": (25.392000, 68.373500),
    "pakka qila": (25.392000, 68.373500),
    "shahi bazaar": (25.392000, 68.373500),
    "autobahn": (25.378000, 68.352000),
    "latifabad unit 2": (25.378000, 68.352000),
    "latifabad unit 7": (25.367000, 68.358000),
    "latifabad unit 9": (25.364000, 68.355000),
    "latifabad": (25.375000, 68.355000),
    "naseem nagar": (25.395000, 68.332000),
    "qasimabad": (25.395000, 68.332000),
    "wadhu wah": (25.405000, 68.338000),
    "haider chowk": (25.391000, 68.362000),
    "saddar": (25.391000, 68.362000),
    "station road": (25.397000, 68.369000),
    "resham gali": (25.397000, 68.369000),
    "kotri barrage": (25.432000, 68.315000),
    "kotri": (25.432000, 68.315000),
    "thandi sarak": (25.402000, 68.356000),
    "hirabad": (25.394000, 68.365000),
    "tower market": (25.394000, 68.365000),
    "citizen colony": (25.388000, 68.341000),
    "site": (25.385000, 68.318000)
}


@app.post("/api/submit-report", response_model=ReportSubmissionResponse, status_code=201, tags=["Citizen Submissions"])
@limiter.limit(settings.SUBMIT_RATE_LIMIT)
async def submit_report(
    request: Request,
    image: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    lat: Optional[str] = Form(None),
    lng: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Resolve coordinates
    resolved_lat: Optional[float] = latitude
    resolved_lon: Optional[float] = longitude

    if resolved_lat is None and lat and lat.strip():
        try:
            resolved_lat = float(lat.strip())
        except ValueError:
            pass
    if resolved_lon is None and lng and lng.strip():
        try:
            resolved_lon = float(lng.strip())
        except ValueError:
            pass

    if resolved_lat is None or resolved_lon is None:
        if address:
            addr_lower = address.lower()
            matched = False
            for k, coords in HYDERABAD_LANDMARKS.items():
                if k in addr_lower:
                    resolved_lat, resolved_lon = coords
                    matched = True
                    break
            if not matched:
                resolved_lat, resolved_lon = 25.392000, 68.358000
        else:
            resolved_lat, resolved_lon = 25.392000, 68.358000

    if not (-90.0 <= resolved_lat <= 90.0) or not (-180.0 <= resolved_lon <= 180.0):
        raise HTTPException(status_code=422, detail="Invalid latitude or longitude coordinate ranges.")

    saved_img = await save_uploaded_file(image, is_image=True)
    saved_aud = await save_uploaded_file(audio, is_image=False) if (audio and audio.filename and audio.size != 0) else None

    combined_text = description or address or ""
    ai_res = process_civic_submission(image_path=saved_img, audio_path=saved_aud, user_description=combined_text)

    # Geo-deduplication check
    dup = find_duplicate_ticket(db, category=ai_res.category, latitude=resolved_lat, longitude=resolved_lon,
                                radius_meters=settings.GEO_DEDUP_RADIUS_METERS, time_window_hours=settings.GEO_DEDUP_TIME_WINDOW_HOURS) if ai_res.is_valid_civic_issue else None

    if dup:
        dup.duplicate_count += 1
        child = Complaint(
            ticket_id=generate_ticket_id(),
            image_path=saved_img,
            original_audio_path=saved_aud,
            translated_text=ai_res.translated_text,
            category=dup.category,
            severity=dup.severity,
            latitude=resolved_lat,
            longitude=resolved_lon,
            ai_action_plan=dup.ai_action_plan,
            is_valid_civic_issue=True,
            status="Open",
            duplicate_of=dup.ticket_id,
            duplicate_count=0
        )
        db.add(child)
        db.commit()
        return ReportSubmissionResponse(
            success=True,
            status="success",
            ticket_id=dup.ticket_id,
            is_duplicate=True,
            merged_ticket_id=dup.ticket_id,
            category=dup.category,
            severity=dup.severity,
            is_valid_civic_issue=True,
            ai_action_plan=dup.ai_action_plan,
            translated_text=ai_res.translated_text,
            message=f"Report merged with active open ticket {dup.ticket_id} within 50m."
        )

    # New primary complaint
    new_id = generate_ticket_id()
    new_c = Complaint(
        ticket_id=new_id,
        image_path=saved_img,
        original_audio_path=saved_aud,
        translated_text=ai_res.translated_text,
        category=ai_res.category,
        severity=ai_res.severity,
        latitude=resolved_lat,
        longitude=resolved_lon,
        ai_action_plan=ai_res.ai_action_plan,
        is_valid_civic_issue=ai_res.is_valid_civic_issue,
        status="Open",
        duplicate_of=None,
        duplicate_count=0
    )
    db.add(new_c)
    db.commit()
    db.refresh(new_c)

    return ReportSubmissionResponse(
        success=True,
        status="success" if new_c.is_valid_civic_issue else "flagged",
        ticket_id=new_c.ticket_id,
        is_duplicate=False,
        merged_ticket_id=None,
        category=new_c.category,
        severity=new_c.severity,
        is_valid_civic_issue=new_c.is_valid_civic_issue,
        ai_action_plan=new_c.ai_action_plan,
        translated_text=new_c.translated_text,
        message="Ticket created and verified successfully." if new_c.is_valid_civic_issue else "Submission received but flagged by AI."
    )


@app.get("/api/tickets", response_model=TicketListResponse, tags=["Municipal Admin"])
def get_tickets(
    status_filter: Optional[StatusEnum] = Query(None, alias="status"),
    category_filter: Optional[CategoryEnum] = Query(None, alias="category"),
    include_invalid: bool = Query(False),
    include_duplicates: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    q = db.query(Complaint)
    if not include_invalid:
        q = q.filter(Complaint.is_valid_civic_issue.is_(True))
    if not include_duplicates:
        q = q.filter(Complaint.duplicate_of.is_(None))
    if status_filter:
        q = q.filter(Complaint.status == status_filter.value)
    if category_filter:
        q = q.filter(Complaint.category == category_filter.value)

    total = q.count()
    raw_tickets = q.order_by(desc(Complaint.timestamp)).offset(offset).limit(limit).all()

    formatted_tickets = []
    for t in raw_tickets:
        formatted_tickets.append(
            TicketResponse(
                ticket_id=t.ticket_id,
                image_path=t.image_path,
                original_audio_path=t.original_audio_path,
                translated_text=t.translated_text,
                category=t.category,
                severity=t.severity,
                latitude=t.latitude,
                longitude=t.longitude,
                lat=t.latitude,
                lng=t.longitude,
                address=t.translated_text or "Hyderabad, Sindh",
                ai_action_plan=t.ai_action_plan,
                is_valid_civic_issue=t.is_valid_civic_issue,
                status=t.status,
                timestamp=t.timestamp,
                created_at=t.timestamp.isoformat(),
                duplicate_of=t.duplicate_of,
                duplicate_count=t.duplicate_count
            )
        )

    return TicketListResponse(total=total, count=len(formatted_tickets), limit=limit, offset=offset, tickets=formatted_tickets)


@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse, tags=["Municipal Admin"])
def get_ticket_detail(ticket_id: str, db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    t = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return t


@app.patch("/api/update-status/{ticket_id}", response_model=TicketResponse, tags=["Municipal Admin"])
def update_status(ticket_id: str, payload: TicketStatusUpdate, db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    t = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    t.status = payload.status.value
    if payload.status.value == "Resolved":
        t.timestamp = datetime.now(timezone.utc)
    db.commit()
    db.refresh(t)
    return TicketResponse(
        ticket_id=t.ticket_id,
        image_path=t.image_path,
        original_audio_path=t.original_audio_path,
        translated_text=t.translated_text,
        category=t.category,
        severity=t.severity,
        latitude=t.latitude,
        longitude=t.longitude,
        lat=t.latitude,
        lng=t.longitude,
        address=t.translated_text or "Hyderabad, Sindh",
        ai_action_plan=t.ai_action_plan,
        is_valid_civic_issue=t.is_valid_civic_issue,
        status=t.status,
        timestamp=t.timestamp,
        created_at=t.timestamp.isoformat(),
        duplicate_of=t.duplicate_of,
        duplicate_count=t.duplicate_count
    )


@app.get("/api/stats", response_model=AdminDashboardStats, tags=["Municipal Admin"])
def get_stats(db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    window_24h = now - timedelta(hours=24)
    effective_start = min(today_start, window_24h)

    base = db.query(Complaint).filter(Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None))

    total_reports = base.count()
    total_open = base.filter(Complaint.status == "Open").count()
    critical_alerts = base.filter(Complaint.status == "Open", Complaint.severity == "Critical").count()
    resolved_today = base.filter(Complaint.status == "Resolved", Complaint.timestamp >= effective_start).count()

    cat_counts = db.query(Complaint.category, func.count(Complaint.ticket_id)).filter(
        Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None)).group_by(Complaint.category).all()
    category_breakdown = {cat: count for cat, count in cat_counts}

    sev_counts = db.query(Complaint.severity, func.count(Complaint.ticket_id)).filter(
        Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None), Complaint.status == "Open").group_by(Complaint.severity).all()
    severity_breakdown = {sev: count for sev, count in sev_counts}

    return AdminDashboardStats(
        total_open=total_open, critical_alerts=critical_alerts, resolved_today=resolved_today,
        total_reports=total_reports, category_breakdown=category_breakdown, severity_breakdown=severity_breakdown
    )


@app.post("/api/seed-demo-data", tags=["Municipal Admin"])
def trigger_seed(db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    count = seed_demo_data(db)
    return {"status": "success", "message": f"Seeded demo dataset successfully. Total active complaints: {count}."}


# ======================================================================================
# 11. MAIN RUNNER (Direct CLI Execution)
# ======================================================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("🚀 Starting CleanCity Copilot Unified Master Backend...")
    print(f"📡 API Documentation:  http://127.0.0.1:{settings.PORT}/docs")
    print(f"🏙️ 3D Web Dashboard:  http://127.0.0.1:{settings.PORT}/")
    print("="*80 + "\n")
    uvicorn.run("master_backend:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
