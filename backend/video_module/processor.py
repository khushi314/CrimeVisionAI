"""
Automated 1Hz Video Frame Extraction (Milestone 4 Activity 4.1).
Uses OpenCV (`cv2.VideoCapture`) when installed, falling back to `ffmpeg` CLI
so 1-frame-per-second extraction works reliably across environments.
"""

import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    from backend.config import PROCESSING_CONFIG, TEMP_DIR
    from backend.utils.logger import setup_logger
except ImportError:
    from config import PROCESSING_CONFIG, TEMP_DIR
    from utils.logger import setup_logger

logger = setup_logger("video_processor")


def extract_frames(video_path: str, sample_fps: float = 1.0) -> Tuple[List[Dict[str, Any]], float]:
    """
    Sample frames from `video_path` at `sample_fps` (default 1Hz = 1 frame/second).
    Returns `(frames_list, duration_seconds)` where each item has `timestamp` and `frame_path`.
    """
    src = Path(video_path)
    if not src.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    max_duration = PROCESSING_CONFIG["max_video_duration_seconds"]
    max_width = PROCESSING_CONFIG["frame_resize_max_width"]
    out_dir = TEMP_DIR / f"vid_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Strategy 1: OpenCV (`cv2`)
    try:
        import cv2

        cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            raise RuntimeError("OpenCV failed to open video stream.")

        native_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = min(float(max_duration), total_frames / max(native_fps, 1.0))
        step = max(1, int(round(native_fps / max(sample_fps, 0.1))))

        extracted: List[Dict[str, Any]] = []
        frame_idx = 0
        sec_idx = 0
        while cap.isOpened() and sec_idx <= int(max_duration):
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                h, w = frame.shape[:2]
                if w > max_width:
                    scale = max_width / float(w)
                    frame = cv2.resize(frame, (max_width, int(h * scale)))
                frame_file = out_dir / f"frame_{sec_idx:03d}.jpg"
                cv2.imwrite(str(frame_file), frame)
                extracted.append({"timestamp": float(sec_idx), "frame_path": str(frame_file)})
                sec_idx += 1
            frame_idx += 1

        cap.release()
        final_dur = max(duration, float(max(0, len(extracted) - 1)))
        return extracted, round(final_dur, 2)
    except ImportError:
        pass

    # Strategy 2: FFmpeg CLI fallback
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        pattern = str(out_dir / "frame_%03d.jpg")
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(src),
            "-t",
            str(max_duration),
            "-vf",
            f"fps={sample_fps},scale='min({max_width},iw)':-2",
            "-q:v",
            "3",
            pattern,
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        files = sorted(out_dir.glob("frame_*.jpg"))
        extracted = [
            {"timestamp": float(idx), "frame_path": str(f_path)}
            for idx, f_path in enumerate(files)
        ]
        duration = float(max(0, len(extracted) - 1))
        return extracted, duration

    logger.warning("Neither OpenCV nor ffmpeg found; returning empty frame sequence.")
    return [], 0.0
