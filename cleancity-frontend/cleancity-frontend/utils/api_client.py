"""
API client for CleanCity Copilot.

Talks to Abdul Latif's FastAPI backend (see Project_Description.docx Section 5):
    POST  /api/submit-report
    GET   /api/tickets
    PATCH /api/update-status/{ticket_id}

Until the backend is live / reachable, every function transparently falls
back to mock data so the frontend team (us) can keep building without being
blocked. Once Latif's server is up, just set BACKEND_URL (env var or below)
-- no other code changes needed.
"""

import os
import requests
import streamlit as st

from utils.mock_data import get_mock_tickets

BACKEND_URL = os.environ.get("CLEANCITY_BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 4  # seconds -- fail fast, fall back to mock


def backend_is_reachable() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=REQUEST_TIMEOUT)
        return r.status_code < 500
    except requests.exceptions.RequestException:
        return False


@st.cache_data(ttl=15, show_spinner=False)
def get_tickets(status: str | None = None, category: str | None = None) -> list[dict]:
    """GET /api/tickets -- returns list of complaint dicts."""
    try:
        params = {}
        if status and status != "All":
            params["status"] = status
        if category and category != "All":
            params["category"] = category
        r = requests.get(f"{BACKEND_URL}/api/tickets", params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        response_data = r.json()
        # Agar data dictionary mein hai toh sirf tickets nikal lo, warna waise hi de do
        return response_data.get("tickets", []) if isinstance(response_data, dict) else response_data
    except requests.exceptions.RequestException:
        # Backend not up yet -- use mock data, apply same filters client-side
        tickets = get_mock_tickets()
        if status and status != "All":
            tickets = [t for t in tickets if t["status"] == status]
        if category and category != "All":
            tickets = [t for t in tickets if t["category"] == category]
        return tickets


def submit_report(image_file, audio_file, description: str, lat: float | None, lng: float | None, address: str) -> dict:
    """POST /api/submit-report -- multipart form (image, audio, lat, lng)."""
    try:
        files = {}
        if image_file is not None:
            files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
        if audio_file is not None:
            files["audio"] = ("voice_note.wav", audio_file.getvalue(), "audio/wav")

        data = {
            "description": description or "",
            "lat": lat if lat is not None else "",
            "lng": lng if lng is not None else "",
            "address": address or "",
        }
        r = requests.post(
            f"{BACKEND_URL}/api/submit-report",
            files=files if files else None,
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException:
        # Mock success response, mirrors expected backend shape
        import random
        return {
            "success": True,
            "ticket_id": f"CC-{random.randint(2000, 2999)}",
            "message": "Report submitted (demo mode -- backend not connected yet).",
            "mock": True,
        }


def update_ticket_status(ticket_id: str, new_status: str) -> dict:
    """PATCH /api/update-status/{ticket_id}"""
    try:
        r = requests.patch(
            f"{BACKEND_URL}/api/update-status/{ticket_id}",
            json={"status": new_status},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        get_tickets.clear()  # invalidate cache
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException:
        get_tickets.clear()
        return {"success": True, "ticket_id": ticket_id, "status": new_status, "mock": True}
