"""
Image Analysis & Complete Multimodal Fusion Pipeline Routes
(`/api/analyze-image`, `/api/process/complete/<case_id>`, `/api/fuse`).
"""

from flask import Blueprint, request, jsonify

try:
    from backend.services.vision_service import VisionService
    from backend.services.audio_service import AudioService
    from backend.services.fusion_service import FusionService
    from backend.services.session_store import session_store
    from backend.utils.file_handler import validate_upload_extension, save_uploaded_bytes
except ImportError:
    from services.vision_service import VisionService
    from services.audio_service import AudioService
    from services.fusion_service import FusionService
    from services.session_store import session_store
    from utils.file_handler import validate_upload_extension, save_uploaded_bytes

processing_bp = Blueprint("processing", __name__, url_prefix="/api")
_vision = VisionService()
_audio = AudioService()
_fusion = FusionService()


@processing_bp.route("/analyze-image", methods=["POST"])
def analyze_image_route():
    """Analyze an uploaded crime scene / forensic photograph and persist session."""
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "Missing 'file' field in multipart upload."}), 400

    uploaded = request.files["file"]
    is_valid, err_msg = validate_upload_extension(uploaded.filename or "", "image")
    if not is_valid:
        return jsonify({"status": "error", "error": err_msg}), 400

    try:
        raw_bytes = uploaded.read()
        saved_path, sha256_hash = save_uploaded_bytes(raw_bytes, uploaded.filename or "scene.jpg", "image")
        result = _vision.analyze_image(str(saved_path))
        result["file_name"] = uploaded.filename
        result["sha256"] = sha256_hash

        case_id = request.form.get("session_id") or None
        session_id = session_store.create_session(result, session_id=case_id)
        result["session_id"] = session_id
        return jsonify({"status": "success", "session_id": session_id, "data": result}), 200
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@processing_bp.route("/fuse", methods=["POST"])
def fuse_sessions_route():
    """Fuse previously analyzed image, audio, and/or video session IDs into a unified record."""
    payload = request.get_json(silent=True) or {}
    img_id = payload.get("image_session_id")
    aud_id = payload.get("audio_session_id")
    vid_id = payload.get("video_session_id")

    img_data = session_store.get_session(img_id) if img_id else payload.get("image_data")
    aud_data = session_store.get_session(aud_id) if aud_id else payload.get("audio_data")
    vid_data = session_store.get_session(vid_id) if vid_id else payload.get("video_data")

    if not any((img_data, aud_data, vid_data)):
        return jsonify({
            "status": "error",
            "error": "Provide at least one analyzed session (image, audio, or video) to fuse.",
        }), 400

    fused = _fusion.fuse_case(img_data, aud_data, vid_data)
    fused_id = session_store.create_session(fused)
    fused["session_id"] = fused_id
    return jsonify({"status": "success", "session_id": fused_id, "data": fused}), 200


@processing_bp.route("/process/complete/<case_id>", methods=["POST"])
def process_complete_pipeline(case_id: str):
    """Run full multimodal pipeline on batch-uploaded files registered under `case_id`."""
    case_record = session_store.get_session(case_id)
    if not case_record or not case_record.get("uploaded_files"):
        return jsonify({"status": "error", "error": f"No uploaded files found for case '{case_id}'."}), 404

    img_res = None
    aud_res = None
    for item in case_record["uploaded_files"]:
        if item["modality"] == "image":
            img_res = _vision.analyze_image(item["saved_path"])
        elif item["modality"] == "audio":
            aud_res = _audio.transcribe_multilingual(item["saved_path"])

    fused = _fusion.fuse_case(image_result=img_res, audio_result=aud_res)
    combined = {
        "case_id": case_id,
        "mode": "fusion",
        "vision_results": img_res,
        "audio_results": aud_res,
        **fused,
    }
    session_store.create_session(combined, session_id=case_id)
    return jsonify({"status": "success", "session_id": case_id, "data": combined}), 200
