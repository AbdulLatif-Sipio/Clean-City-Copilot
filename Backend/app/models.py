import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, Boolean, DateTime, Integer, Index
from app.database import Base


def generate_ticket_id() -> str:
    """Generate a unique human-friendly ticket ID, e.g., TKT-A8F12C."""
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"TKT-{short_uuid}"


class Complaint(Base):
    """
    SQLAlchemy ORM model representing citizen civic issue complaints.
    """
    __tablename__ = "complaints"

    ticket_id = Column(
        String(32),
        primary_key=True,
        index=True,
        default=generate_ticket_id,
        doc="Unique ticket identifier"
    )
    image_path = Column(
        String(512),
        nullable=False,
        doc="Local filesystem path to the uploaded image"
    )
    original_audio_path = Column(
        String(512),
        nullable=True,
        doc="Local filesystem path to the uploaded voice note"
    )
    translated_text = Column(
        Text,
        nullable=True,
        doc="English text transcribed/translated from audio or citizen text input"
    )
    category = Column(
        String(32),
        nullable=False,
        default="Unassigned",
        index=True,
        doc="Civic issue category (Garbage, Pothole, Sewerage, Unassigned)"
    )
    severity = Column(
        String(16),
        nullable=False,
        default="Medium",
        index=True,
        doc="Severity score (Critical, High, Medium, Low, Unknown)"
    )
    latitude = Column(
        Float,
        nullable=False,
        doc="GPS Latitude coordinate"
    )
    longitude = Column(
        Float,
        nullable=False,
        doc="GPS Longitude coordinate"
    )
    ai_action_plan = Column(
        Text,
        nullable=True,
        doc="Actionable AI recommendation for tools and crew deployment"
    )
    is_valid_civic_issue = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="True if validated as a genuine civic issue, False for spam/selfies"
    )
    status = Column(
        String(16),
        nullable=False,
        default="Open",
        index=True,
        doc="Status of ticket (Open, In Progress, Resolved)"
    )
    timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
        doc="UTC timestamp of submission"
    )
    duplicate_of = Column(
        String(32),
        nullable=True,
        doc="Reference ticket_id if this complaint was merged as a geo-duplicate"
    )
    duplicate_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of additional citizen reports merged into this ticket"
    )

    __table_args__ = (
        # Composite index for high-speed spatial-temporal geo-deduplication queries
        Index("ix_complaints_geo_time", "latitude", "longitude", "timestamp"),
        # Composite index for high-speed admin dashboard filtering
        Index("ix_complaints_admin_filter", "status", "category", "is_valid_civic_issue"),
    )

    def __repr__(self) -> str:
        return f"<Complaint(ticket_id={self.ticket_id}, category={self.category}, severity={self.severity}, status={self.status})>"
