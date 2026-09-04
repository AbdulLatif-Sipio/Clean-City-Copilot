from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator


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


class CoordinateValidationMixin(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="GPS Latitude (-90.0 to 90.0)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="GPS Longitude (-180.0 to 180.0)")


class TicketResponse(BaseModel):
    """
    Standard serialized response for a single ticket / complaint.
    Includes lat, lng, created_at for seamless frontend compatibility.
    """
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
    """
    Paginated response for admin tickets list.
    """
    total: int
    count: int
    limit: int
    offset: int
    tickets: List[TicketResponse]


class TicketStatusUpdate(BaseModel):
    """
    Request schema for PATCH /api/update-status/{ticket_id}
    """
    status: StatusEnum

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        if isinstance(value, str):
            # Allow case-insensitive or hyphenated matching
            val_norm = value.strip().title()
            if val_norm == "In-Progress":
                return "In Progress"
            return val_norm
        return value


class ReportSubmissionResponse(BaseModel):
    """
    Response returned to citizen or client after POST /api/submit-report
    """
    success: bool = True
    status: str = Field(..., description="'success' or 'flagged'")
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
    """
    High-level metric cards for the Streamlit Municipal Admin Dashboard.
    """
    total_open: int
    critical_alerts: int
    resolved_today: int
    total_reports: int
    category_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
