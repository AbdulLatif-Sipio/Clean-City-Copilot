import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import verify_admin_api_key
from app.database import get_db
from app.seed import seed_demo_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Municipal Admin Tools"])


@router.post(
    "/seed-demo-data",
    summary="Seed demo complaints dataset (Admin)",
    description="Instantly populates the database with realistic Karachi civic complaints for live demos."
)
def trigger_seed_demo_data(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    count = seed_demo_data(db)
    logger.info(f"Demo data seeded: {count} complaints present.")
    return {
        "status": "success",
        "message": f"Seeded demo dataset successfully. Total active complaints: {count}."
    }
