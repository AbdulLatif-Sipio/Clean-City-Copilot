"""
Mock data for CleanCity Copilot frontend.
Used as a fallback whenever the FastAPI backend (Abdul Latif's service) is
not reachable, so the UI is always demo-able -- during dev, at the hackathon
judging table, or in offline screenshots.

Shape of a "ticket" mirrors what GET /api/tickets is expected to return
(see Project_Description.docx, Section 5).
"""

from datetime import datetime, timedelta
import random

CATEGORIES = ["Garbage", "Pothole", "Sewerage"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
STATUSES = ["Open", "In Progress", "Resolved"]

SEVERITY_COLOR = {
    "Critical": "#DC2626",
    "High": "#F59E0B",
    "Medium": "#EAB308",
    "Low": "#22C55E",
}

CATEGORY_ICON = {
    "Garbage": "🗑️",
    "Pothole": "🕳️",
    "Sewerage": "🚱",
}

_LOCATIONS = [
    ("Latifabad Unit 9, Hyderabad", 25.3792, 68.3683),
    ("Qasimabad, Hyderabad", 25.4231, 68.3903),
    ("Auto Bhan Road, Hyderabad", 25.3897, 68.3540),
    ("Hirabad, Hyderabad", 25.3833, 68.3667),
    ("Mirpurkhas City Center", 25.5271, 69.0113),
    ("Tando Adam Bypass", 25.7667, 68.6614),
    ("Saddar, Hyderabad", 25.3960, 68.3730),
    ("Cantonment Area, Hyderabad", 25.3707, 68.3745),
]

_REASONING = {
    "Garbage": "Large garbage accumulation visible, partially blocking pedestrian path and posing a health hazard.",
    "Pothole": "Significant road surface damage detected, deep enough to risk vehicle and rider safety.",
    "Sewerage": "Visible sewage overflow onto the street, standing water with contamination risk.",
}

_ACTION = {
    "Garbage": "Requires 1 dump truck and 2-3 sanitation workers.",
    "Pothole": "Requires road repair crew with asphalt patching materials.",
    "Sewerage": "Requires sewerage line inspection team and suction pump vehicle.",
}


def _make_ticket(i: int) -> dict:
    loc_name, lat, lng = random.choice(_LOCATIONS)
    category = random.choice(CATEGORIES)
    severity = random.choices(SEVERITIES, weights=[1, 2, 3, 2])[0]
    status = random.choices(STATUSES, weights=[3, 2, 2])[0]
    created = datetime.now() - timedelta(hours=random.randint(1, 96))

    return {
        "ticket_id": f"CC-{1000 + i}",
        "category": category,
        "severity": severity,
        "status": status,
        "location_name": loc_name,
        "lat": lat + random.uniform(-0.01, 0.01),
        "lng": lng + random.uniform(-0.01, 0.01),
        "created_at": created,
        "reasoning": _REASONING[category],
        "recommended_action": _ACTION[category],
        "transcribed_note": "Gali ke nukkad pe masla hai, jaldi theek karwayein.",
        "is_valid_civic_issue": True,
        "duplicate_count": random.choice([0, 0, 0, 1, 2]),
        "image_url": None,  # placeholder -- real image comes from backend
    }


def get_mock_tickets(n: int = 24) -> list[dict]:
    random.seed(42)  # stable demo data across reruns
    return [_make_ticket(i) for i in range(n)]
