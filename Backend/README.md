# 🚀 CleanCity Copilot — Unified Backend Engine & Built-in 3D UI

CleanCity Copilot is an AI-assisted civic issue triage and routing engine built for the **Alibaba Cloud AI Hackathon 2026**.

This repository contains the complete **Unified FastAPI Backend** featuring:
- 🚀 **High-Performance REST APIs** with Pydantic v2 validation.
- 🗄️ **Zero-Cost SQLite Database Layer** with Write-Ahead Logging (WAL) and composite spatial indexes.
- 🌍 **Haversine Geo-Deduplication Engine** (50m radius / 48hr window).
- 🤖 **Multimodal AI Integration Stubs** (Whisper Audio STT + Vision LLM with offline fallback).
- 🏙️ **Built-in 3D Cyberpunk Web Dashboard** served directly at `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/dashboard` without needing any separate frontend services!
- 📚 **Interactive Swagger API Docs** at `http://127.0.0.1:8000/docs`.

---

## 🏛 Architecture & Key Design Decisions

### 1. Database & ORM: SQLAlchemy 2.0 + SQLite
- **Why**: Zero-cost, zero external cloud database dependencies, 100% offline-ready for live demo day.
- **Security**: Built entirely with SQLAlchemy ORM and parameterized queries to prevent SQL injection vulnerabilities.
- **Performance**: High-speed composite indexes on `(latitude, longitude, timestamp)` for spatial-temporal deduplication and `(status, category, is_valid_civic_issue)` for instantaneous admin dashboard filtering. SQLite Write-Ahead Logging (WAL) is enabled for fast concurrent read/write throughput.

### 2. Authentication Strategy: API Key Header (`X-Admin-API-Key`)
- **Public Submission**: `POST /api/submit-report` requires no authentication so citizens can submit issues frictionlessly without login hurdles.
- **Admin Endpoints**: `GET /api/tickets`, `GET /api/tickets/{id}`, `PATCH /api/update-status/{id}`, and `GET /api/stats` are strictly protected by an `X-Admin-API-Key` header.
- **Security Hardening**: Compared using `secrets.compare_digest` to prevent side-channel timing attacks. Configured via the `ADMIN_API_KEY` environment variable.

### 3. AI Pipeline Integration: Synchronous Execution with Configurable Stubs
- **Decision**: Synchronous processing with typed integration boundaries and offline mock fallbacks.
- **Why**: In a hackathon demo, immediate feedback is critical. When a citizen submits a photo, the Streamlit frontend instantly receives the AI-classified category, severity score, and actionable repair crew recommendations in the response payload without requiring complex polling loops.
- **Integration Boundary**: Syed Fazeel's Whisper & Vision LLM models integrate cleanly in [`app/ai_integration.py`](app/ai_integration.py). If an external API is offline or unconfigured, an intelligent heuristic fallback executes automatically, guaranteeing uninterrupted live demos.

### 4. Geo-Deduplication Engine (Haversine 50m / 48hr Window)
- Calculates great-circle distance between coordinates using the Haversine formula ($R = 6,371,000 \text{ m}$).
- Checks if an active **Open** issue of the **same category** already exists within **50.0 meters** reported in the last **48.0 hours**.
- If a duplicate is found, the submission is attached to the existing ticket (incrementing `duplicate_count`) and returns `is_duplicate: true` with the original `ticket_id`.
- Rigorously boundary-tested for edge cases ($49.9\text{m}$ vs $50.1\text{m}$).

---

## 📂 Project Structure

```
├── app/
│   ├── __init__.py
│   ├── config.py             # Pydantic Settings (.env configuration)
│   ├── database.py           # SQLAlchemy engine, session maker, WAL pragmas
│   ├── models.py             # Complaint model & composite indexes
│   ├── schemas.py            # Pydantic request/response schemas & Enums
│   ├── auth.py               # Timing-safe Admin API Key dependency
│   ├── geo.py                # Haversine distance & spatial-temporal dedup
│   ├── ai_integration.py     # AI Pipeline integration stubs (Whisper + Vision LLM)
│   ├── utils/
│   │   └── file_handler.py   # Upload validation, MIME allowlists, UUID filenames
│   ├── routers/
│   │   ├── submissions.py    # POST /api/submit-report
│   │   ├── tickets.py        # GET /api/tickets, PATCH /api/update-status/{id}
│   │   └── stats.py          # GET /api/stats (Admin Dashboard metrics)
│   └── main.py               # FastAPI app factory, CORS, Rate Limiting, Lifespan
├── media/
│   ├── images/               # Stored citizen issue photos
│   └── audio/                # Stored voice notes (Urdu/Roman Urdu)
├── tests/
│   ├── __init__.py
│   ├── test_geo.py           # Haversine & 50m boundary test suite
│   └── test_api.py           # End-to-end API, auth, upload & rate-limit tests
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🛠 Local Setup & Running

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)

### 2. Installation
```bash
# Clone repository and enter directory
cd "Clean-City-Copilot"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` settings:
```ini
ADMIN_API_KEY=cleancity-admin-secret-key-2026
SUBMIT_RATE_LIMIT=30/minute
GEO_DEDUP_RADIUS_METERS=50.0
GEO_DEDUP_TIME_WINDOW_HOURS=48.0
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

### 4. Start Backend Server (FastAPI)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger API Docs: **http://127.0.0.1:8000/docs**
- Alternative ReDoc: **http://127.0.0.1:8000/redoc**

### 5. Start 3D UI/UX Frontend (Streamlit)
In a separate terminal:
```bash
streamlit run backend/app.py --server.port 8501
```
- **3D Citizen & Admin Web Portal**: **http://localhost:8501**
- Switch between **Citizen Report Portal** and **Municipal Admin 3D Dashboard** using the left sidebar!

---

## 🧪 Running Automated Tests

Run the complete test suite (Geo boundary verification + API integration tests):
```bash
pytest -v
```

---

## 📡 API Endpoints & cURL Examples

### 1. Submit Citizen Report (`POST /api/submit-report`)
*Public endpoint (no auth required). Accepts multipart form data with rate limiting.*

```bash
curl -X POST "http://127.0.0.1:8000/api/submit-report" \
  -F "image=@sample_garbage.jpg;type=image/jpeg" \
  -F "audio=@voice_note.mp3;type=audio/mpeg" \
  -F "latitude=24.861460" \
  -F "longitude=67.026150" \
  -F "description=Kachra jama hai gali ke konay par"
```

**Response (201 Created)**:
```json
{
  "status": "success",
  "ticket_id": "TKT-A8F12C",
  "is_duplicate": false,
  "merged_ticket_id": null,
  "category": "Garbage",
  "severity": "High",
  "is_valid_civic_issue": true,
  "ai_action_plan": "Requires 1 dump truck and 3 sanitation workers for 2 hours.",
  "translated_text": "Reported overflowing garbage pile near the street corner requiring cleanup.",
  "message": "Ticket created and verified successfully."
}
```

---

### 2. List & Filter Tickets (`GET /api/tickets`)
*Admin endpoint. Requires `X-Admin-API-Key` header.*

```bash
curl -X GET "http://127.0.0.1:8000/api/tickets?status=Open&category=Garbage&limit=20" \
  -H "X-Admin-API-Key: cleancity-admin-secret-key-2026"
```

**Response (200 OK)**:
```json
{
  "total": 14,
  "count": 14,
  "limit": 20,
  "offset": 0,
  "tickets": [
    {
      "ticket_id": "TKT-A8F12C",
      "image_path": "media/images/a41b2...jpg",
      "original_audio_path": "media/audio/99b1...mp3",
      "translated_text": "Reported overflowing garbage pile...",
      "category": "Garbage",
      "severity": "High",
      "latitude": 24.861460,
      "longitude": 67.026150,
      "ai_action_plan": "Requires 1 dump truck and 3 sanitation workers for 2 hours.",
      "is_valid_civic_issue": true,
      "status": "Open",
      "timestamp": "2026-08-31T03:30:00Z",
      "duplicate_of": null,
      "duplicate_count": 3
    }
  ]
}
```

---

### 3. Update Ticket Status (`PATCH /api/update-status/{ticket_id}`)
*Admin endpoint. Allowed statuses: `"Open"`, `"In Progress"`, `"Resolved"`.*

```bash
curl -X PATCH "http://127.0.0.1:8000/api/update-status/TKT-A8F12C" \
  -H "X-Admin-API-Key: cleancity-admin-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress"}'
```

**Response (200 OK)**:
```json
{
  "ticket_id": "TKT-A8F12C",
  "status": "In Progress",
  "category": "Garbage",
  "severity": "High",
  "latitude": 24.861460,
  "longitude": 67.026150,
  "is_valid_civic_issue": true,
  "ai_action_plan": "Requires 1 dump truck and 3 sanitation workers for 2 hours."
}
```

---

### 4. Admin Dashboard Metrics (`GET /api/stats`)
*Admin endpoint for top summary metric cards on Streamlit dashboard.*

```bash
curl -X GET "http://127.0.0.1:8000/api/stats" \
  -H "X-Admin-API-Key: cleancity-admin-secret-key-2026"
```

**Response (200 OK)**:
```json
{
  "total_open": 18,
  "critical_alerts": 4,
  "resolved_today": 7,
  "total_reports": 42,
  "category_breakdown": {
    "Garbage": 10,
    "Pothole": 5,
    "Sewerage": 3
  },
  "severity_breakdown": {
    "Critical": 4,
    "High": 9,
    "Medium": 5
  }
}
```

---

## 🔒 Security Hardening Summary

| Security Layer | Implementation Details |
|---|---|
| **SQL Injection Prevention** | 100% ORM parameterized queries via SQLAlchemy 2.0. |
| **Authentication** | Timing-attack resistant `secrets.compare_digest` on `X-Admin-API-Key`. |
| **DDoS / Abuse Prevention** | Rate limiting on public submission endpoint (`slowapi`). |
| **Malicious Upload Defense** | MIME allowlisting, streaming 10MB size limit, server-side UUID filenames. |
| **Input Sanitization** | Strict Pydantic models, coordinate clamping $[-90, 90]$ and $[-180, 180]$, and Enum validation. |
| **Information Disclosure** | Generic client error responses; real stack traces isolated to server logs. |
| **CORS Restriction** | Whitelisted frontend origins only (no wildcard `*` allowed). |
