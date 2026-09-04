import os
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import Complaint
from app.utils.file_handler import ensure_upload_dirs

# 12 Real Hyderabad, Sindh Landmarks & Detailed Civic Complaints
HYDERABAD_DEMO_COMPLAINTS = [
    {
        "category": "Garbage",
        "severity": "Critical",
        "latitude": 25.392000,
        "longitude": 68.373500,
        "location_name": "Pacco Qillo (Pakka Qila), Shahi Bazaar Gate",
        "description": "Pacco Qillo main entrance ke samnay Shahi Bazaar market ka shadeed kachra jama hai, tourists aur public traffic block ho rahi hai.",
        "translated_text": "Massive solid waste accumulation blocking the main historical entrance of Pacco Qillo near Shahi Bazaar.",
        "ai_action_plan": "Deploy 2 heavy dumpers, 1 mini-loader excavator, and 6 sanitation workers for 3 hours.",
        "status": "Open",
        "duplicate_count": 5,
        "is_valid_civic_issue": True
    },
    {
        "category": "Pothole",
        "severity": "Critical",
        "latitude": 25.378000,
        "longitude": 68.352000,
        "location_name": "Autobahn Road, Latifabad Unit 2",
        "description": "Autobahn Road main commercial strip par gehra crater pothole ban chuka hai, motorcycle riders gir rahay hain.",
        "translated_text": "Deep hazardous road crater on Autobahn Road Latifabad posing high risk of accidents for two-wheelers.",
        "ai_action_plan": "Deploy 1 rapid asphalt cold-mix repair truck and 2 highway patch technicians.",
        "status": "Open",
        "duplicate_count": 4,
        "is_valid_civic_issue": True
    },
    {
        "category": "Sewerage",
        "severity": "Critical",
        "latitude": 25.395000,
        "longitude": 68.332000,
        "location_name": "Naseem Nagar Chowk, Qasimabad",
        "description": "Naseem Nagar chowk par main sewerage drain choke ho chuki hai, ganda paani commercial dukano ke andar ghus raha hai.",
        "translated_text": "Severe municipal sewerage overflow at Naseem Nagar Chowk Qasimabad submerging commercial shops.",
        "ai_action_plan": "Deploy 2 high-capacity suction jetting tankers and 4 WASA drainage technicians.",
        "status": "Open",
        "duplicate_count": 6,
        "is_valid_civic_issue": True
    },
    {
        "category": "Garbage",
        "severity": "High",
        "latitude": 25.367000,
        "longitude": 68.358000,
        "location_name": "Latifabad Unit 7, Near General Hospital",
        "description": "Hospital gate ke samnay waste disposal dump overflow ho raha hai, infection ka khatra hai.",
        "translated_text": "Decomposing waste accumulation near Latifabad Unit 7 General Hospital walkway.",
        "ai_action_plan": "Deploy 1 compact compactor truck and 3 municipal sanitation workers.",
        "status": "In Progress",
        "duplicate_count": 2,
        "is_valid_civic_issue": True
    },
    {
        "category": "Pothole",
        "severity": "High",
        "latitude": 25.405000,
        "longitude": 68.338000,
        "location_name": "Wadhu Wah Road, Qasimabad",
        "description": "Wadhu Wah road par drainage excavation ke baad tooti hui sarak ka malba pada hai.",
        "translated_text": "Extensive road surface fractures and loose gravel on Wadhu Wah Road Qasimabad.",
        "ai_action_plan": "Schedule asphalt leveling crew and road rolling machinery.",
        "status": "In Progress",
        "duplicate_count": 2,
        "is_valid_civic_issue": True
    },
    {
        "category": "Sewerage",
        "severity": "Medium",
        "latitude": 25.391000,
        "longitude": 68.362000,
        "location_name": "Haider Chowk / Saddar Hyderabad",
        "description": "Haider Chowk traffic signal ke paas storm drain block honay se badbu aur water stagnation hai.",
        "translated_text": "Storm drain blockage near Haider Chowk Saddar causing stagnant street water and odor.",
        "ai_action_plan": "Deploy manual drain rodding team to clear commercial trash obstruction.",
        "status": "Resolved",
        "duplicate_count": 1,
        "is_valid_civic_issue": True
    },
    {
        "category": "Garbage",
        "severity": "High",
        "latitude": 25.397000,
        "longitude": 68.369000,
        "location_name": "Station Road / Resham Gali",
        "description": "Resham Gali market packaging waste aur plastic bags ka dher laga hua hai.",
        "translated_text": "Market packing refuse and plastic debris along Station Road / Resham Gali market avenue.",
        "ai_action_plan": "Deploy night-shift mechanical sweeper and waste disposal truck.",
        "status": "Open",
        "duplicate_count": 3,
        "is_valid_civic_issue": True
    },
    {
        "category": "Pothole",
        "severity": "Critical",
        "latitude": 25.432000,
        "longitude": 68.315000,
        "location_name": "Kotri Barrage Indus Bridge Approach",
        "description": "Kotri Barrage bridge approach road par multiple deep potholes hain, freight trucks ka bumper lag raha hai.",
        "translated_text": "Multiple deep structural potholes on Kotri Barrage approach road damaging heavy vehicles.",
        "ai_action_plan": "Emergency road patching crew with heavy asphalt paver.",
        "status": "Open",
        "duplicate_count": 7,
        "is_valid_civic_issue": True
    },
    {
        "category": "Garbage",
        "severity": "Medium",
        "latitude": 25.402000,
        "longitude": 68.356000,
        "location_name": "Thandi Sarak / Hyderabad Gymkhana",
        "description": "Thandi Sarak green belt ke qareeb lawn pruning aur organic leaves ka kachra pada hai.",
        "translated_text": "Organic refuse and tree pruning debris left on Thandi Sarak green median near Gymkhana.",
        "ai_action_plan": "Deploy horticultural waste collection vehicle.",
        "status": "Resolved",
        "duplicate_count": 0,
        "is_valid_civic_issue": True
    },
    {
        "category": "Pothole",
        "severity": "High",
        "latitude": 25.394000,
        "longitude": 68.365000,
        "location_name": "Hirabad / Tower Market Chowk",
        "description": "Hirabad roundabout ke ird gird tooti hui sarak aur khadday hain.",
        "translated_text": "Fractured road asphalt around Hirabad Tower Market roundabout.",
        "ai_action_plan": "Apply cold-patch asphalt filler and compact surface.",
        "status": "Open",
        "duplicate_count": 2,
        "is_valid_civic_issue": True
    },
    {
        "category": "Sewerage",
        "severity": "High",
        "latitude": 25.388000,
        "longitude": 68.341000,
        "location_name": "Citizen Colony, Qasimabad",
        "description": "Citizen Colony residential street main sewer line backflow mar rahi hai.",
        "translated_text": "Residential sewer line backflow causing street flooding in Citizen Colony Qasimabad.",
        "ai_action_plan": "Deploy municipal jetting tanker to flush pipeline blockage.",
        "status": "Open",
        "duplicate_count": 3,
        "is_valid_civic_issue": True
    },
    {
        "category": "Garbage",
        "severity": "Critical",
        "latitude": 25.385000,
        "longitude": 68.318000,
        "location_name": "SITE Industrial Area Hyderabad",
        "description": "SITE area main road par industrial solid waste aur scrap illegally dump kiya gaya hai.",
        "translated_text": "Illegal industrial solid waste dump blocking primary access lane in SITE Hyderabad.",
        "ai_action_plan": "Dispatch heavy wheel-loader and two 20-ton dumper trucks with EPA inspection officer.",
        "status": "In Progress",
        "duplicate_count": 4,
        "is_valid_civic_issue": True
    }
]


def seed_demo_data(db: Session = None, force_reset: bool = False) -> int:
    """
    Seed 12 realistic Hyderabad, Sindh civic complaint records for live demo.
    """
    ensure_upload_dirs()
    init_db()

    close_db_at_end = False
    if db is None:
        db = SessionLocal()
        close_db_at_end = True

    created_count = 0
    now = datetime.now(timezone.utc)

    try:
        if force_reset:
            db.query(Complaint).delete()
            db.commit()
        else:
            existing = db.query(Complaint).count()
            if existing >= len(HYDERABAD_DEMO_COMPLAINTS):
                return existing

        sample_img_path = "media/images/hyderabad_demo_sample.jpg"
        if not os.path.exists(sample_img_path):
            with open(sample_img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 400)

        for i, item in enumerate(HYDERABAD_DEMO_COMPLAINTS):
            if item["status"] == "Resolved":
                item_time = now - timedelta(hours=random.randint(1, 3))
            elif item["status"] == "In Progress":
                item_time = now - timedelta(hours=random.randint(4, 12))
            else:
                item_time = now - timedelta(hours=random.randint(6, 36))

            ticket = Complaint(
                ticket_id=f"HYD-TKT-10{i+1:02d}",
                image_path=sample_img_path,
                original_audio_path=None,
                translated_text=item["translated_text"],
                category=item["category"],
                severity=item["severity"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                ai_action_plan=item["ai_action_plan"],
                is_valid_civic_issue=item["is_valid_civic_issue"],
                status=item["status"],
                timestamp=item_time,
                duplicate_of=None,
                duplicate_count=item["duplicate_count"]
            )
            db.add(ticket)
            created_count += 1

        db.commit()
    finally:
        if close_db_at_end:
            db.close()

    return created_count


if __name__ == "__main__":
    count = seed_demo_data(force_reset=True)
    print(f"Successfully seeded {count} Hyderabad, Sindh civic issues into CleanCity Copilot SQLite database!")
