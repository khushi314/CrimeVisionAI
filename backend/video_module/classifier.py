"""
Temporal Crime Sequence Classifier (Milestone 4 Activity 4.2).
Classifies sequential frame detections & captions into objective activity categories
(e.g., NORMAL ACTIVITY, SUSPICIOUS REMOVAL / THEFT INDICATOR, ARMED DISTURBANCE)
with an explicit `reason` and non-accusatory framing.
"""

import json
from typing import List, Dict, Any

try:
    from backend.utils.groq_utils import generate_grounded_completion
except ImportError:
    from utils.groq_utils import generate_grounded_completion


def classify_crime(
    captions: List[Dict[str, Any]],
    aggregated: Dict[str, Any],
    location: str,
) -> Dict[str, Any]:
    """Classify overall video incident status from sequential captions and object counts."""
    prompt = (
        "Analyze this sequential CCTV detection log and return strict JSON with keys: "
        '"classification" (e.g., "NORMAL ACTIVITY", "POTENTIAL THEFT INDICATOR", "POTENTIAL ASSAULT / ARMED ALERT"), '
        '"action" (short action label e.g. "routine browsing", "rapid item removal", "none"), '
        '"confidence" (float 0.0-1.0), and '
        '"reason" (concise factual justification).\n\n'
        f"Location: {location}\n"
        f"Aggregated Objects: {aggregated}\n"
        f"Captions: {captions[:15]}"
    )
    llm_raw = generate_grounded_completion(prompt, temperature=0.1)
    if llm_raw:
        try:
            s_idx = llm_raw.find("{")
            e_idx = llm_raw.rfind("}")
            if s_idx != -1 and e_idx != -1:
                parsed = json.loads(llm_raw[s_idx : e_idx + 1])
                if "classification" in parsed:
                    return parsed
        except Exception:
            pass

    weapons_count = int(aggregated.get("weapons_count", 0))
    joined_caps = " ".join(c.get("caption", "").lower() for c in captions)

    if weapons_count > 0:
        return {
            "classification": "POTENTIAL WEAPON / SAFETY ALERT",
            "action": "weapon-like object present",
            "confidence": 0.82,
            "reason": "Weapon-category object detected in one or more sampled video frames; human review required.",
        }

    if any(k in joined_caps for k in ("running", "runs", "rushed", "grabbed", "grabs", "forced", "fleeing")):
        return {
            "classification": "SUSPICIOUS RAPID MOVEMENT",
            "action": "rapid exit / item handling",
            "confidence": 0.74,
            "reason": "Sequential frames show rapid movement or abrupt object handling.",
        }

    return {
        "classification": "NORMAL ACTIVITY",
        "action": "none",
        "confidence": 0.88,
        "reason": "No explicit crime or weapon indicator observed across sampled surveillance frames.",
    }
