import logging
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.database import get_db
from app.models import Complaint, generate_ticket_id
from app.schemas import ReportSubmissionResponse
from app.utils.file_handler import save_uploaded_file
from app.geo import find_duplicate_ticket
from app.ai_integration import process_civic_submission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Citizen Submissions"])
limiter = Limiter(key_func=get_remote_address)

# Hyderabad, Sindh Landmark Geocoding Dictionary (Fallback for text address inputs)
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


@router.post(
    "/submit-report",
    response_model=ReportSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a citizen civic issue report",
    description="Public endpoint for citizens to report garbage, pothole, or sewage issues with image, optional audio/text, and GPS coordinates."
)
@limiter.limit(settings.SUBMIT_RATE_LIMIT)
async def submit_report(
    request: Request,
    image: UploadFile = File(..., description="Civic issue image file (JPEG, PNG, WebP)"),
    audio: Optional[UploadFile] = File(None, description="Optional Urdu/Roman Urdu voice note (MP3, WAV, M4A, OGG)"),
    latitude: Optional[float] = Form(None, description="GPS Latitude (-90.0 to 90.0)"),
    longitude: Optional[float] = Form(None, description="GPS Longitude (-180.0 to 180.0)"),
    lat: Optional[str] = Form(None, description="Frontend alias for Latitude"),
    lng: Optional[str] = Form(None, description="Frontend alias for Longitude"),
    address: Optional[str] = Form(None, description="Street address or nearest landmark"),
    description: Optional[str] = Form(None, description="Optional manual text description"),
    db: Session = Depends(get_db)
):
    # 1. Resolve and Validate Coordinates (Support latitude/longitude or lat/lng or address geocode)
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

    # If coordinates are still missing, geocode from address string
    if resolved_lat is None or resolved_lon is None:
        if address:
            addr_lower = address.lower()
            matched = False
            for landmark_key, coords in HYDERABAD_LANDMARKS.items():
                if landmark_key in addr_lower:
                    resolved_lat, resolved_lon = coords
                    matched = True
                    break
            if not matched:
                # Default to Hyderabad City Center (Haider Chowk)
                resolved_lat, resolved_lon = 25.392000, 68.358000
        else:
            resolved_lat, resolved_lon = 25.392000, 68.358000

    # Server-Side Coordinate Range Validation
    if not (-90.0 <= resolved_lat <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Latitude must be between -90.0 and 90.0. Received {resolved_lat}."
        )
    if not (-180.0 <= resolved_lon <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Longitude must be between -180.0 and 180.0. Received {resolved_lon}."
        )

    # 2. Validate and Save Image
    saved_image_path = await save_uploaded_file(image, is_image=True)

    # 3. Validate and Save Optional Audio Note
    saved_audio_path: Optional[str] = None
    if audio and audio.filename and audio.size != 0:
        saved_audio_path = await save_uploaded_file(audio, is_image=False)

    # 4. Invoke AI Engine (Audio STT -> Multimodal Vision & Logic)
    try:
        combined_text = description or address or ""
        ai_result = process_civic_submission(
            image_path=saved_image_path,
            audio_path=saved_audio_path,
            user_description=combined_text
        )
    except Exception as e:
        logger.error(f"AI Pipeline execution error: {e}", exc_info=True)
        ai_result = process_civic_submission(
            image_path=saved_image_path,
            audio_path=None,
            user_description=description or address or ""
        )

    # 5. Spatial-Temporal Geo-Deduplication (50-meter radius, 48 hours)
    duplicate_ticket: Optional[Complaint] = None
    if ai_result.is_valid_civic_issue:
        duplicate_ticket = find_duplicate_ticket(
            db=db,
            category=ai_result.category,
            latitude=resolved_lat,
            longitude=resolved_lon,
            radius_meters=settings.GEO_DEDUP_RADIUS_METERS,
            time_window_hours=settings.GEO_DEDUP_TIME_WINDOW_HOURS
        )

    if duplicate_ticket:
        # Existing open ticket found within 50m! Merge this report.
        duplicate_ticket.duplicate_count += 1
        
        child_complaint = Complaint(
            ticket_id=generate_ticket_id(),
            image_path=saved_image_path,
            original_audio_path=saved_audio_path,
            translated_text=ai_result.translated_text,
            category=duplicate_ticket.category,
            severity=duplicate_ticket.severity,
            latitude=resolved_lat,
            longitude=resolved_lon,
            ai_action_plan=duplicate_ticket.ai_action_plan,
            is_valid_civic_issue=True,
            status="Open",
            duplicate_of=duplicate_ticket.ticket_id,
            duplicate_count=0
        )
        db.add(child_complaint)
        db.commit()

        logger.info(f"Report merged into existing ticket {duplicate_ticket.ticket_id} (Duplicate count: {duplicate_ticket.duplicate_count})")

        return ReportSubmissionResponse(
            success=True,
            status="success",
            ticket_id=duplicate_ticket.ticket_id,
            is_duplicate=True,
            merged_ticket_id=duplicate_ticket.ticket_id,
            category=duplicate_ticket.category,
            severity=duplicate_ticket.severity,
            is_valid_civic_issue=True,
            ai_action_plan=duplicate_ticket.ai_action_plan,
            translated_text=ai_result.translated_text,
            message=f"Report verified! Merged with existing active issue within 50m at {duplicate_ticket.ticket_id}."
        )

    # 6. No duplicate found: Create new primary ticket
    new_ticket_id = generate_ticket_id()
    new_complaint = Complaint(
        ticket_id=new_ticket_id,
        image_path=saved_image_path,
        original_audio_path=saved_audio_path,
        translated_text=ai_result.translated_text,
        category=ai_result.category,
        severity=ai_result.severity,
        latitude=resolved_lat,
        longitude=resolved_lon,
        ai_action_plan=ai_result.ai_action_plan,
        is_valid_civic_issue=ai_result.is_valid_civic_issue,
        status="Open",
        duplicate_of=None,
        duplicate_count=0
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    logger.info(f"New ticket created: {new_ticket_id} [Category: {new_complaint.category}, Severity: {new_complaint.severity}]")

    return ReportSubmissionResponse(
        success=True,
        status="success" if new_complaint.is_valid_civic_issue else "flagged",
        ticket_id=new_complaint.ticket_id,
        is_duplicate=False,
        merged_ticket_id=None,
        category=new_complaint.category,
        severity=new_complaint.severity,
        is_valid_civic_issue=new_complaint.is_valid_civic_issue,
        ai_action_plan=new_complaint.ai_action_plan,
        translated_text=new_complaint.translated_text,
        message="Ticket created and verified successfully." if new_complaint.is_valid_civic_issue else "Submission received but flagged by AI as invalid civic issue (selfie/unrelated)."
    )
