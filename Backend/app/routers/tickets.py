import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.auth import verify_admin_api_key
from app.database import get_db
from app.models import Complaint
from app.schemas import (
    TicketResponse,
    TicketListResponse,
    TicketStatusUpdate,
    CategoryEnum,
    StatusEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Municipal Admin Dashboard"])


@router.get(
    "/tickets",
    response_model=TicketListResponse,
    summary="Get all civic issue tickets",
    description="Retrieve a paginated list of complaints with optional status and category filters."
)
def get_tickets(
    status_filter: Optional[StatusEnum] = Query(None, alias="status", description="Filter by status (Open, In Progress, Resolved)"),
    category_filter: Optional[CategoryEnum] = Query(None, alias="category", description="Filter by category (Garbage, Pothole, Sewerage)"),
    include_invalid: bool = Query(False, description="Whether to include tickets flagged as invalid by AI (default false)"),
    include_duplicates: bool = Query(False, description="Whether to include merged duplicate submissions (default false)"),
    limit: int = Query(100, ge=1, le=500, description="Max tickets to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    query = db.query(Complaint)

    # By default, exclude invalid spam/selfie submissions unless explicitly requested
    if not include_invalid:
        query = query.filter(Complaint.is_valid_civic_issue.is_(True))

    # By default, return primary tickets only
    if not include_duplicates:
        query = query.filter(Complaint.duplicate_of.is_(None))

    # Optional status filter
    if status_filter:
        query = query.filter(Complaint.status == status_filter.value)

    # Optional category filter
    if category_filter:
        query = query.filter(Complaint.category == category_filter.value)

    total = query.count()
    raw_tickets = query.order_by(desc(Complaint.timestamp)).offset(offset).limit(limit).all()

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

    return TicketListResponse(
        total=total,
        count=len(formatted_tickets),
        limit=limit,
        offset=offset,
        tickets=formatted_tickets
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Get ticket details by ID",
    description="Fetch single complaint ticket details by ticket ID."
)
def get_ticket_by_id(
    ticket_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    ticket = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found."
        )
    return ticket


@router.patch(
    "/update-status/{ticket_id}",
    response_model=TicketResponse,
    summary="Update ticket status",
    description="Update the status of a ticket (Open, In Progress, Resolved)."
)
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    from datetime import datetime, timezone
    ticket = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found."
        )

    ticket.status = payload.status.value
    if payload.status.value == "Resolved":
        ticket.timestamp = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)

    logger.info(f"Admin updated ticket {ticket_id} status to '{ticket.status}'")

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        image_path=ticket.image_path,
        original_audio_path=ticket.original_audio_path,
        translated_text=ticket.translated_text,
        category=ticket.category,
        severity=ticket.severity,
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        lat=ticket.latitude,
        lng=ticket.longitude,
        address=ticket.translated_text or "Hyderabad, Sindh",
        ai_action_plan=ticket.ai_action_plan,
        is_valid_civic_issue=ticket.is_valid_civic_issue,
        status=ticket.status,
        timestamp=ticket.timestamp,
        created_at=ticket.timestamp.isoformat(),
        duplicate_of=ticket.duplicate_of,
        duplicate_count=ticket.duplicate_count
    )
