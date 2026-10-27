"""
File validation, secure naming, and SHA-256 forensic integrity hashing.
Ensures invalid or unsupported uploads fail gracefully with clear messages.
"""

import hashlib
import re
import uuid
from pathlib import Path
from typing import Tuple, Set

try:
    from backend.config import PROCESSING_CONFIG, UPLOADS_DIR
except ImportError:
    from config import PROCESSING_CONFIG, UPLOADS_DIR


def sanitize_filename(filename: str) -> str:
    """Sanitize an uploaded filename without requiring external C extensions."""
    cleaned = Path(filename or "").name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned.strip("._") or f"evidence_{uuid.uuid4().hex[:8]}"


def validate_upload_extension(filename: str, modality: str) -> Tuple[bool, str]:
    """
    Validate that the file has a non-empty name and a supported extension
    for the requested modality ('image', 'audio', or 'video').
    """
    if not filename or not filename.strip():
        return False, "No filename provided in upload request."

    ext = Path(filename).suffix.lower()
    allowed_map: dict[str, Set[str]] = {
        "image": PROCESSING_CONFIG["allowed_image_extensions"],
        "audio": PROCESSING_CONFIG["allowed_audio_extensions"],
        "video": PROCESSING_CONFIG["allowed_video_extensions"],
    }

    allowed = allowed_map.get(modality)
    if allowed is None:
        return False, f"Unsupported analysis modality '{modality}'."

    if ext not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        return False, f"Unsupported {modality} file format '{ext or 'none'}'. Allowed formats: {allowed_list}."

    return True, ""


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of an evidence file for chain-of-custody verification."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_uploaded_bytes(raw_bytes: bytes, original_filename: str, modality: str) -> Tuple[Path, str]:
    """Save uploaded bytes to the modality upload folder and return (path, sha256)."""
    if not raw_bytes:
        raise ValueError("Uploaded file is empty (0 bytes).")

    target_dir = UPLOADS_DIR / modality
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:8]}_{sanitize_filename(original_filename)}"
    saved_path = target_dir / safe_name
    saved_path.write_bytes(raw_bytes)
    return saved_path, compute_sha256(saved_path)
