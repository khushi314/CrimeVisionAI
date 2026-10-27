"""
CrimeVision AI — Official Python Flask Backend Entry Point (`backend/app.py`).

Implements:
- Runtime environment guards (`PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION`, `USE_TF=0`)
  specified in Milestone 1 of the official project workflow.
- Blueprint registration for Image, Audio, Video, Batch Upload, Multimodal Fusion,
  Grounded Forensic Chat, and Downloadable PDF Reports.
- `/api/health` endpoint for automated verification (`test_validation.py`).
"""

import os

# Milestone 1 runtime guards to prevent protobuf / TensorFlow conflicts with PyTorch
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("USE_TF", "0")

import sys
from pathlib import Path
from typing import Dict, Any

# Ensure repository root is importable whether invoked as `python backend/app.py` or `python -m backend.app`
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import API_CONFIG, SAMPLES_DIR
from backend.utils.logger import setup_logger
from backend.utils.model_loader import resolve_device

logger = setup_logger("crimevision_app")


def get_health_payload() -> Dict[str, Any]:
    """Return standardized system health payload for `/api/health` and unit tests."""
    return {
        "status": "healthy",
        "service": "CrimeVision AI Forensic Backend",
        "version": "1.0.0",
        "device": resolve_device(),
        "modules": {
            "vision": "ready",
            "audio": "ready",
            "video": "ready",
            "fusion": "ready",
            "chat": "ready",
            "report": "ready",
        },
    }


def create_app():
    """Create and configure the Flask application with all forensic Blueprints."""
    from flask import Flask, jsonify, send_from_directory

    try:
        from flask_cors import CORS
    except ImportError:
        CORS = None

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = API_CONFIG["max_content_length_mb"] * 1024 * 1024

    if CORS is not None:
        CORS(app, resources={r"/api/*": {"origins": API_CONFIG["cors_origins"]}})

    from backend.routes.upload_routes import upload_bp
    from backend.routes.processing_routes import processing_bp
    from backend.routes.results_routes import results_bp
    from backend.routes.chat_routes import chat_bp
    from backend.audio_module.api import audio_analysis_bp
    from backend.video_module.api import video_analysis_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(audio_analysis_bp)
    app.register_blueprint(video_analysis_bp)

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify(get_health_payload()), 200

    @app.route("/samples/<path:subpath>", methods=["GET"])
    def serve_sample_asset(subpath: str):
        return send_from_directory(str(SAMPLES_DIR), subpath)

    @app.errorhandler(413)
    def handle_payload_too_large(_err):
        return (
            jsonify({
                "status": "error",
                "error": f"Uploaded file exceeds maximum allowed size ({API_CONFIG['max_content_length_mb']} MB).",
            }),
            413,
        )

    return app


if __name__ == "__main__":
    flask_app = create_app()
    logger.info(
        "Starting CrimeVision AI Flask server on %s:%s",
        API_CONFIG["host"],
        API_CONFIG["port"],
    )
    flask_app.run(
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
    )
