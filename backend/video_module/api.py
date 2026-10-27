"""
Flask Blueprint for Surveillance Video Analysis (`/api/analyze-video`).
Orchestrates 1Hz frame extraction, RT-DETR detection, CLIP location classification,
frame captioning, crime sequence classification, and hash-indexed timeline building.
"""

from flask import Blueprint, request, jsonify

try:
    from backend.video_module.processor import extract_frames
    from backend.video_module.detector import detect_objects_in_frames, aggregate_objects
    from backend.video_module.captions import generate_frame_captions, summarize_captions
    from backend.video_module.classifier import classify_crime
    from backend.video_module.timeline import build_timeline
    from backend.services.vision_service import VisionService
    from backend.services.session_store import session_store
    from backend.utils.file_handler import validate_upload_extension, save_uploaded_bytes
    from backend.utils.groq_utils import get_groq_client, get_config
except ImportError:
    from video_module.processor import extract_frames
    from video_module.detector import detect_objects_in_frames, aggregate_objects
    from video_module.captions import generate_frame_captions, summarize_captions
    from video_module.classifier import classify_crime
    from video_module.timeline import build_timeline
    from services.vision_service import VisionService
    from services.session_store import session_store
    from utils.file_handler import validate_upload_extension, save_uploaded_bytes
    from utils.groq_utils import get_groq_client, get_config

video_analysis_bp = Blueprint("video_analysis", __name__, url_prefix="/api/analyze-video")
_vision = VisionService()


@video_analysis_bp.route("", methods=["POST"])
def analyze_video():
    """Main endpoint for CCTV / forensic video analysis."""
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "Missing 'file' field in multipart upload."}), 400

    uploaded = request.files["file"]
    is_valid, err_msg = validate_upload_extension(uploaded.filename or "", "video")
    if not is_valid:
        return jsonify({"status": "error", "error": err_msg}), 400

    try:
        raw_bytes = uploaded.read()
        saved_path, sha256_hash = save_uploaded_bytes(raw_bytes, uploaded.filename or "video.mp4", "video")

        frames, duration = extract_frames(str(saved_path), sample_fps=1.0)
        location = "surveillance area"
        if frames:
            loc_info = _vision.classify_location(frames[0]["frame_path"])
            location = loc_info["location"]

        frame_detections = detect_objects_in_frames(frames)
        aggregated = aggregate_objects(frame_detections)
        captions = generate_frame_captions(frames, frame_detections, location)
        visual_summary = summarize_captions(captions, duration, location)
        classification_info = classify_crime(captions, aggregated, location)
        timeline_bundle = build_timeline(
            captions,
            frame_detections,
            groq_client=get_groq_client(),
            config=get_config(),
            duration=duration,
        )

        result = {
            "mode": "video",
            "file_name": uploaded.filename,
            "sha256": sha256_hash,
            "duration_seconds": duration,
            "classification": classification_info.get("classification", "NORMAL ACTIVITY"),
            "classification_reason": classification_info.get("reason", ""),
            "classification_confidence": classification_info.get("confidence", 0.85),
            "visual_summary": visual_summary,
            "scene_intelligence": {
                "objects_detected": aggregated["objects_detected"],
                "people_count": aggregated["people_count"],
                "weapons_count": aggregated["weapons_count"],
                "location": location,
                "action": classification_info.get("action", "none"),
            },
            "timeline": timeline_bundle["timeline"],
        }

        case_id = request.form.get("session_id") or None
        session_id = session_store.create_session(result, session_id=case_id)
        result["session_id"] = session_id
        return jsonify({"status": "success", "session_id": session_id, "data": result}), 200
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500
