from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.auth import verify_admin_api_key
from app.database import get_db
from app.models import Complaint
from app.schemas import AdminDashboardStats

router = APIRouter(prefix="/api", tags=["Municipal Admin Dashboard"])


@router.get(
    "/stats",
    response_model=AdminDashboardStats,
    summary="Get aggregated dashboard statistics (Admin)",
    description="Returns metrics for the admin dashboard top cards: Total Open Issues, Critical Alerts, Resolved Today, and category/severity breakdown."
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    # Calculate today's window (handling UTC and local timezone differences)
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    window_24h = now - timedelta(hours=24)
    effective_start = min(today_start, window_24h)

    # Base query for valid primary complaints
    base_query = db.query(Complaint).filter(
        Complaint.is_valid_civic_issue.is_(True),
        Complaint.duplicate_of.is_(None)
    )

    total_reports = base_query.count()
    total_open = base_query.filter(Complaint.status == "Open").count()
    critical_alerts = base_query.filter(
        Complaint.status == "Open",
        Complaint.severity == "Critical"
    ).count()

    resolved_today = base_query.filter(
        Complaint.status == "Resolved",
        Complaint.timestamp >= effective_start
    ).count()

    # Category breakdown for Open tickets
    category_counts = (
        db.query(Complaint.category, func.count(Complaint.ticket_id))
        .filter(Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None))
        .group_by(Complaint.category)
        .all()
    )
    category_breakdown = {cat: count for cat, count in category_counts}

    # Severity breakdown for Open tickets
    severity_counts = (
        db.query(Complaint.severity, func.count(Complaint.ticket_id))
        .filter(Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None), Complaint.status == "Open")
        .group_by(Complaint.severity)
        .all()
    )
    severity_breakdown = {sev: count for sev, count in severity_counts}

    return AdminDashboardStats(
        total_open=total_open,
        critical_alerts=critical_alerts,
        resolved_today=resolved_today,
        total_reports=total_reports,
        category_breakdown=category_breakdown,
        severity_breakdown=severity_breakdown
    )
