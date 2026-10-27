"""
Centralized configuration for the CrimeVision AI backend.
Keeps model identifiers, thresholds, file limits, and directory paths
separate from core inference and routing logic.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
TEMP_DIR = DATA_DIR / "temp_frames"
SESSIONS_DIR = DATA_DIR / "sessions"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"

for directory in (UPLOADS_DIR, TEMP_DIR, SESSIONS_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

API_CONFIG: Dict[str, Any] = {
    "host": os.getenv("FLASK_HOST", "0.0.0.0"),
    "port": int(os.getenv("FLASK_PORT", "5000")),
    "debug": os.getenv("FLASK_DEBUG", "false").lower() == "true",
    "max_content_length_mb": 50,
    "cors_origins": os.getenv("CORS_ORIGINS", "*"),
}

MODEL_CONFIG: Dict[str, Any] = {
    "device_preference": os.getenv("FORENSIC_DEVICE", "auto"),
    "lightweight_mode": os.getenv("CRIMEVISION_LIGHTWEIGHT_MODE", "false").lower() == "true",
    "rt_detr": {
        "model_id": os.getenv("RTDETR_MODEL_ID", "PekingU/rtdetr_r50vd"),
        "confidence_threshold": float(os.getenv("RTDETR_CONFIDENCE", "0.45")),
        "weapon_labels": {"knife", "scissors", "baseball bat", "gun", "handgun", "rifle", "weapon"},
        "person_labels": {"person", "human", "man", "woman", "individual"},
    },
    "clip": {
        "model_id": os.getenv("CLIP_MODEL_ID", "openai/clip-vit-base-patch32"),
        "candidate_locations": [
            "office",
            "bedroom",
            "living room hall",
            "kitchen",
            "retail store",
            "shopping mall store",
            "street or road",
            "parking lot",
            "warehouse",
            "alleyway",
        ],
    },
    "blip2": {
        "model_id": os.getenv("BLIP_MODEL_ID", "Salesforce/blip-image-captioning-large"),
        "max_new_tokens": 64,
    },
    "whisper": {
        "model_id": os.getenv("WHISPER_MODEL_ID", "openai/whisper-base"),
        "supported_languages": ["en", "hi", "te", "fr"],
    },
    "sam": {
        "checkpoint_path": os.getenv("SAM_CHECKPOINT_PATH", ""),
        "model_type": "vit_b",
    },
    "groq": {
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "temperature": 0.1,
        "max_tokens": 1024,
    },
}

PROCESSING_CONFIG: Dict[str, Any] = {
    "allowed_image_extensions": {".jpg", ".jpeg", ".png", ".webp", ".bmp"},
    "allowed_audio_extensions": {".wav", ".mp3", ".m4a", ".ogg", ".flac"},
    "allowed_video_extensions": {".mp4", ".avi", ".mov", ".mkv", ".webm"},
    "video_sample_fps": 1.0,  # 1Hz second-by-second sampling per workflow spec
    "max_video_duration_seconds": 30,
    "frame_resize_max_width": 960,
    "audio_timeout_seconds": 120,
}
