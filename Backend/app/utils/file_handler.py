import os
import uuid
from typing import Tuple, Set, Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings

# Strict MIME type allowlists
ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

ALLOWED_AUDIO_TYPES: Set[str] = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/x-m4a",
    "audio/m4a",
    "audio/mp4",
    "audio/webm",
}

# Mapping of content types to safe extensions
MIME_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/x-m4a": ".m4a",
    "audio/m4a": ".m4a",
    "audio/mp4": ".m4a",
    "audio/webm": ".webm",
}


def ensure_upload_dirs() -> None:
    """Ensure media directories exist on the local filesystem."""
    os.makedirs(settings.IMAGE_SUBDIR, exist_ok=True)
    os.makedirs(settings.AUDIO_SUBDIR, exist_ok=True)


async def save_uploaded_file(
    file: UploadFile,
    is_image: bool = True
) -> str:
    """
    Validates and saves an uploaded file to disk with a secure server-generated UUID filename.
    
    Security Protections:
    - Rejects disallowed MIME types.
    - Limits total uploaded bytes to MAX_UPLOAD_SIZE_BYTES (10MB) during streaming.
    - Uses server-generated UUID for filename to eliminate path traversal and injection risks.

    :param file: FastAPI UploadFile object.
    :param is_image: True if validating as an image, False if validating as an audio file.
    :return: Local filesystem path where file is saved.
    """
    ensure_upload_dirs()

    # 1. Content-Type Validation
    content_type = (file.content_type or "").lower().strip()
    allowed_types = ALLOWED_IMAGE_TYPES if is_image else ALLOWED_AUDIO_TYPES
    target_dir = settings.IMAGE_SUBDIR if is_image else settings.AUDIO_SUBDIR
    file_label = "Image" if is_image else "Audio"

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {file_label.lower()} file type '{content_type}'. Allowed types: {sorted(list(allowed_types))}"
        )

    # 2. Determine safe file extension
    ext = MIME_EXTENSION_MAP.get(content_type, ".bin")
    if file.filename:
        _, raw_ext = os.path.splitext(file.filename)
        if raw_ext and raw_ext.lower() in [".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".ogg", ".m4a", ".webm"]:
            ext = raw_ext.lower()

    # 3. Generate server-side random filename
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    destination_path = os.path.join(target_dir, unique_filename)

    # 4. Stream write with size limit checking to protect memory & disk
    total_bytes = 0
    chunk_size = 64 * 1024  # 64KB chunks

    try:
        with open(destination_path, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up partial file on violation
                    buffer.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"{file_label} file size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
                    )
                buffer.write(chunk)
    finally:
        await file.seek(0)  # Reset file pointer if needed

    # Normalize path with forward slashes for cross-platform compatibility
    return destination_path.replace("\\", "/")
