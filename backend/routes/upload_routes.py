"""Universal single and batch evidence upload routes (`/api/upload`)."""

import uuid
from flask import Blueprint, request, jsonify

try:
    from backend.utils.file_handler import validate_upload_extension, save_uploaded_bytes
    from backend.services.session_store import session_store
except ImportError:
    from utils.file_handler import validate_upload_extension, save_uploaded_bytes
    from services.session_store import session_store

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")


def _infer_modality(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
        return "image"
    if lower.endswith((".wav", ".mp3", ".m4a", ".ogg", ".flac")):
        return "audio"
    if lower.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
        return "video"
    return "unknown"


@upload_bp.route("", methods=["POST"])
def upload_batch():
    """Accept one or more evidence files, validate formats, compute SHA-256, and register case."""
    files = request.files.getlist("files") or (
        [request.files["file"]] if "file" in request.files else []
    )
    if not files:
        return jsonify({"status": "error", "error": "No evidence files provided."}), 400

    case_id = request.form.get("case_id") or str(uuid.uuid4())
    saved_items = []

    for f_obj in files:
        fname = f_obj.filename or ""
        modality = _infer_modality(fname)
        if modality == "unknown":
            return jsonify({"status": "error", "error": f"Unsupported file type for '{fname}'."}), 400

        valid, msg = validate_upload_extension(fname, modality)
        if not valid:
            return jsonify({"status": "error", "error": msg}), 400

        raw = f_obj.read()
        path, sha256 = save_uploaded_bytes(raw, fname, modality)
        saved_items.append({
            "original_name": fname,
            "modality": modality,
            "saved_path": str(path),
            "sha256": sha256,
            "size_bytes": len(raw),
        })

    session_store.update_session(case_id, {"case_id": case_id, "uploaded_files": saved_items})
    return jsonify({"status": "success", "case_id": case_id, "files": saved_items}), 200
