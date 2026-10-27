"""
Sequential Frame Captioning & Visual Summary Synthesis (Milestone 4 Activity 4.1 & 4.2).
"""

from typing import List, Dict, Any

try:
    from backend.services.vision_service import VisionService
    from backend.utils.groq_utils import generate_grounded_completion
except ImportError:
    from services.vision_service import VisionService
    from utils.groq_utils import generate_grounded_completion

_vision_service = VisionService()


def generate_frame_captions(
    frames: List[Dict[str, Any]],
    frame_detections: List[Dict[str, Any]],
    location: str,
) -> List[Dict[str, Any]]:
    """Generate a natural-language caption for each sampled second of footage."""
    det_by_sec = {int(d["timestamp"]): d["detections"] for d in frame_detections}
    captions: List[Dict[str, Any]] = []
    for frame in frames:
        sec = int(frame["timestamp"])
        dets = det_by_sec.get(sec, [])
        cap = _vision_service.generate_caption(frame["frame_path"], dets, location)
        captions.append({
            "timestamp": float(sec),
            "caption": cap,
        })
    return captions


def summarize_captions(captions: List[Dict[str, Any]], duration: float, location: str) -> str:
    """Synthesize frame-level captions into an overarching AI Visual Summary paragraph."""
    if not captions:
        return "No video frames could be sampled from the uploaded surveillance clip."

    joined = "\n".join(f"[{int(c['timestamp']):02d}s] {c['caption']}" for c in captions[:20])
    prompt = (
        f"Synthesize this {int(duration)}-second surveillance frame log from a {location} "
        "into a clear 2-3 sentence objective AI Visual Summary:\n"
        f"{joined}"
    )
    llm_summary = generate_grounded_completion(prompt, temperature=0.1)
    if llm_summary:
        return llm_summary

    first_cap = captions[0]["caption"]
    last_cap = captions[-1]["caption"]
    return (
        f"Surveillance footage spanning {int(max(1, duration))} seconds in a {location}. "
        f"Initial frame shows: {first_cap} Final sampled frame shows: {last_cap}"
    )
