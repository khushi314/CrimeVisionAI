"""
Flask Blueprint for Audio Analysis (`/api/analyze-audio`).
Validates audio format, runs Whisper + crime intelligence extraction, and persists session.
"""

from flask import Blueprint, request, jsonify

try:
    from backend.audio_module.transcription import process_witness_audio
    from backend.services.session_store import session_store
    from backend.utils.file_handler import validate_upload_extension, save_uploaded_bytes
except ImportError:
    from audio_module.transcription import process_witness_audio
    from services.session_store import session_store
    from utils.file_handler import validate_upload_extension, save_uploaded_bytes

audio_analysis_bp = Blueprint("audio_analysis", __name__, url_prefix="/api/analyze-audio")


@audio_analysis_bp.route("", methods=["POST"])
def analyze_audio():
    """Main endpoint for witness statement audio analysis."""
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "Missing 'file' field in multipart upload."}), 400

    uploaded = request.files["file"]
    is_valid, err_msg = validate_upload_extension(uploaded.filename or "", "audio")
    if not is_valid:
        return jsonify({"status": "error", "error": err_msg}), 400

    try:
        raw_bytes = uploaded.read()
        saved_path, sha256_hash = save_uploaded_bytes(raw_bytes, uploaded.filename or "audio.wav", "audio")
        result = process_witness_audio(str(saved_path))
        result["file_name"] = uploaded.filename
        result["sha256"] = sha256_hash

        case_id = request.form.get("session_id") or None
        session_id = session_store.create_session(result, session_id=case_id)
        result["session_id"] = session_id
        return jsonify({"status": "success", "session_id": session_id, "data": result}), 200
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500
