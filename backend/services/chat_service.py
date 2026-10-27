"""
Forensic Chat Service — Regex Time-Based Direct Lookup & Grounded RAG Answering
(Milestone 5 Activity 5.2 & Milestone 6).
"""

import json
import re
from typing import Dict, Any, Optional, List

try:
    from backend.services.session_store import session_store
    from backend.utils.groq_utils import generate_grounded_completion
except ImportError:
    from services.session_store import session_store
    from utils.groq_utils import generate_grounded_completion


def parse_time_from_question(question: str) -> Optional[int]:
    """
    Detect explicit timestamp queries such as 'at 00:05', 'at 12s', 'at 7 seconds',
    or '1:04' using regular expressions.
    """
    if not question:
        return None

    # Pattern 1: MM:SS (e.g. "00:08" or "1:15")
    mm_ss = re.search(r"\b(\d{1,2}):(\d{2})\b", question)
    if mm_ss:
        minutes = int(mm_ss.group(1))
        seconds = int(mm_ss.group(2))
        return minutes * 60 + seconds

    # Pattern 2: Explicit seconds (e.g. "5s", "12 sec", "at second 4", "8 seconds")
    sec_match = re.search(
        r"(?:\bat\s+|\bsecond\s+)(\d{1,3})\b|\b(\d{1,3})\s*(?:s|sec|secs|second|seconds)\b",
        question.lower(),
    )
    if sec_match:
        val = sec_match.group(1) or sec_match.group(2)
        return int(val)

    return None


def get_event_at_time(timeline: List[Dict[str, Any]], target_sec: int) -> str:
    """Return the exact or closest +/-2s event from a structured timeline."""
    if not timeline:
        return "Information not found in timeline."

    for item in timeline:
        if int(round(float(item.get("seconds", -999)))) == target_sec:
            return f"At {item.get('time', f'{target_sec:02d}s')}: {item.get('event', 'No activity recorded.')}"

    # Nearest event within 3 seconds
    closest = min(
        timeline,
        key=lambda item: abs(float(item.get("seconds", 0)) - target_sec),
    )
    if abs(float(closest.get("seconds", 0)) - target_sec) <= 3.0:
        return (
            f"Closest recorded timestamp ({closest.get('time')}): "
            f"{closest.get('event', 'No significant activity')}"
        )

    return f"Information not found for timestamp {target_sec // 60:02d}:{target_sec % 60:02d}."


def query_chat(session_id: str, question: str, mode: str = "video") -> str:
    """
    Query stored forensic context for `session_id`.
    1. In video/audio/fusion modes, prioritizes direct deterministic timeline lookup
       if a timestamp is referenced.
    2. Otherwise executes strictly grounded RAG prompting (no hallucination).
    """
    if not question or not question.strip():
        return "Please enter a specific forensic question about the analyzed evidence."

    context = session_store.get_session(session_id)
    if not context:
        return "Session context not found. Please run analysis on an evidence file first."

    detected_sec = parse_time_from_question(question)
    timeline = context.get("timeline") or context.get("unified_timeline") or []
    if detected_sec is not None and mode in ("video", "audio", "fusion") and timeline:
        return get_event_at_time(timeline, detected_sec)

    prompt = (
        "Answer based ONLY on these forensic analysis results:\n"
        f"{json.dumps(context, default=str)}\n\n"
        'Rule: Do NOT hallucinate. If not found in the evidence context, say "Information not found in the analyzed evidence."\n'
        "Rule: Maintain objective, non-accusatory forensic language.\n"
        f"Answer concisely: {question}"
    )
    llm_answer = generate_grounded_completion(prompt, temperature=0.1)
    if llm_answer:
        return llm_answer

    return _deterministic_context_answer(context, question, mode)


def _deterministic_context_answer(context: Dict[str, Any], question: str, mode: str) -> str:
    q = question.lower()
    if any(k in q for k in ("summary", "happened", "overview", "describe")):
        if context.get("ai_scene_summary"):
            s = context["ai_scene_summary"]
            return f"{s.get('summary_type', 'Summary')}: {s.get('brief_description', '')}"
        if context.get("ai_summary"):
            return str(context["ai_summary"])
        if context.get("visual_summary"):
            return str(context["visual_summary"])

    if any(k in q for k in ("object", "item", "seen", "detect", "weapon", "evidence")):
        items = (
            context.get("evidence_facts")
            or context.get("scene_intelligence", {}).get("objects_detected")
            or context.get("facts", {}).get("actions")
        )
        if items:
            return f"Cataloged items/observations in this {mode} session: {', '.join(str(x) for x in items)}."

    if any(k in q for k in ("where", "location", "place", "room")):
        loc = (
            context.get("location")
            or context.get("scene_intelligence", {}).get("location")
            or (context.get("facts", {}).get("where") or [None])[0]
        )
        if loc:
            return f"Estimated scene location: {loc}."

    if any(k in q for k in ("person", "people", "human", "who", "count")):
        counts = context.get("counts") or {}
        if "persons" in counts:
            return f"Detected persons count: {counts['persons']} (total cataloged objects: {counts.get('objects', 0)})."
        p_count = context.get("scene_intelligence", {}).get("people_count")
        if p_count is not None:
            return f"Observed people count across sampled frames: {p_count}."

    if any(k in q for k in ("scenario", "hypothesis", "hypotheses")):
        scenarios = context.get("scenarios") or []
        if scenarios:
            formatted = [
                f"{s['title']}: {s['description']}" if isinstance(s, dict) else str(s)
                for s in scenarios
            ]
            return " | ".join(formatted)

    return "Information not found in the analyzed evidence."
