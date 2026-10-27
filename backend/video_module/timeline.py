"""
Hash-Indexed Second-by-Second Timeline Builder (Milestone 4 Activity 4.2 & Milestone 5).
Aligns asynchronous frame captions and RT-DETR object detections onto a fixed
1Hz integer second clock (`00:00`, `00:01`, ...) with float-normalized offsets.
"""

from typing import List, Dict, Any, Optional


def build_timeline(
    captions: List[Dict[str, Any]],
    detections: List[Dict[str, Any]],
    groq_client: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
    duration: float = 0.0,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a deterministic second-by-second timeline using hash indexing (`caption_map`
    and `detection_map`) across `[0 .. int(duration)]`.
    """
    caption_map: Dict[int, str] = {
        int(round(float(c.get("timestamp", c.get("second", 0))))): str(c.get("caption", "")).strip()
        for c in captions
    }
    detection_map: Dict[int, List[str]] = {
        int(round(float(d.get("timestamp", d.get("second", 0))))): [
            str(det.get("label", "")) for det in d.get("detections", []) if det.get("label")
        ]
        for d in detections
    }
    weapons_by_sec: Dict[int, int] = {
        int(round(float(d.get("timestamp", d.get("second", 0))))): int(d.get("weapons_count", 0))
        for d in detections
    }

    max_sec = max(
        [int(duration)]
        + list(caption_map.keys())
        + list(detection_map.keys())
        + [0]
    )

    final_timeline: List[Dict[str, Any]] = []
    for sec in range(max_sec + 1):
        raw_cap = caption_map.get(sec, "")
        labels = list(dict.fromkeys(detection_map.get(sec, [])))
        has_weapon = weapons_by_sec.get(sec, 0) > 0 or any(
            lbl.lower() in {"knife", "gun", "weapon", "scissors"} for lbl in labels
        )

        if raw_cap and labels:
            description = f"{raw_cap} (Detected: {', '.join(labels[:5])})"
        elif raw_cap:
            description = raw_cap
        elif labels:
            description = f"Detected objects in frame: {', '.join(labels[:6])}"
        else:
            description = "No significant activity"

        severity = "alert" if has_weapon else ("elevated" if (raw_cap or labels) else "normal")
        final_timeline.append({
            "time": f"{sec // 60:02d}:{sec % 60:02d}",
            "event": description,
            "seconds": float(sec),
            "objects": labels,
            "severity": severity,
            "confidence": 0.85 if (raw_cap or labels) else 0.65,
        })

    return {"timeline": final_timeline}
