import secrets
from typing import Optional
from fastapi import Security
from fastapi.security import APIKeyHeader
from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def verify_admin_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Zero-friction Hackathon mode: API key requirement is removed!
    Allows seamless, direct testing in Swagger (/docs), Streamlit frontend,
    and Postman without getting 401 errors.
    """
    if api_key_header:
        return api_key_header
    return "authorized-admin"
