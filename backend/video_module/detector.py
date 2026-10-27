"""
Sequential Frame Object Detection & Aggregation using VisionService / RT-DETR
(Milestone 4 Activity 4.1).
"""

from typing import List, Dict, Any

try:
    from backend.services.vision_service import VisionService
except ImportError:
    from services.vision_service import VisionService

_vision_service = VisionService()


def detect_objects_in_frames(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run RT-DETR object detection on every sampled 1Hz video frame."""
    frame_detections: List[Dict[str, Any]] = []
    for frame in frames:
        ts = float(frame["timestamp"])
        det_res = _vision_service.detect_objects(frame["frame_path"])
        frame_detections.append({
            "timestamp": ts,
            "detections": det_res["detections"],
            "counts": det_res["counts"],
        })
    return frame_detections


def aggregate_objects(frame_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate unique detected objects, peak person count, and weapon indicators across video."""
    unique_objects: List[str] = []
    max_people = 0
    max_weapons = 0

    for item in frame_detections:
        counts = item.get("counts", {})
        max_people = max(max_people, int(counts.get("persons", 0)))
        max_weapons = max(max_weapons, int(counts.get("weapons", 0)))
        for det in item.get("detections", []):
            lbl = det.get("label", "")
            if lbl and lbl not in unique_objects:
                unique_objects.append(lbl)

    return {
        "objects_detected": unique_objects,
        "people_count": max_people,
        "weapons_count": max_weapons,
    }
