"""
Multimodal Fusion Service — Temporal Alignment, Cross-Modal Consistency Audit,
Forensic Certainty Scoring, and Unified Narrative Synthesis
(Milestone 5: Activities 5.1 & 5.2).
"""

import json
from typing import List, Dict, Any, Optional

try:
    from backend.utils.logger import setup_logger
    from backend.utils.groq_utils import generate_grounded_completion
except ImportError:
    from utils.logger import setup_logger
    from utils.groq_utils import generate_grounded_completion

logger = setup_logger("fusion_service")


class FusionService:
    """Fuses vision, audio, and video outputs onto a unified chronological forensic axis."""

    def _check_consistency(
        self,
        vision_results: List[Dict[str, Any]],
        audio_results: List[Dict[str, Any]],
        text_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Cross-Modal Audit: Corroborates visual scene locations/objects against
        auditory witness statements and optional text entities.
        """
        text_results = text_results or []
        consistency: Dict[str, Any] = {
            "overall_score": 0.0,
            "matches": [],
            "conflicts": [],
        }

        vision_locs = {
            str(res.get("location", "")).strip().lower()
            for res in vision_results
            if res.get("location")
        }
        audio_locs = {
            str(loc).strip().lower()
            for res in audio_results
            for loc in res.get("facts", {}).get("locations", [])
            if loc and str(loc).strip().lower() != "unknown"
        }
        text_locs = {
            str(loc).strip().lower()
            for res in text_results
            for loc in res.get("entities", {}).get("locations", [])
            if loc
        }

        all_sources = [s for s in (vision_locs, audio_locs, text_locs) if s]
        if len(all_sources) >= 2:
            # Check pairwise overlap including substring match (e.g. "store" vs "retail store")
            matched_locs = set()
            for loc_a in all_sources[0]:
                for other_set in all_sources[1:]:
                    for loc_b in other_set:
                        if loc_a == loc_b or loc_a in loc_b or loc_b in loc_a:
                            matched_locs.add(loc_a)

            if matched_locs:
                for m in sorted(matched_locs):
                    consistency["matches"].append(f"Corroborated spatial location across modalities: '{m}'")
            else:
                consistency["conflicts"].append(
                    f"Location discrepancy across modalities: { [sorted(list(s)) for s in all_sources] }"
                )

        # Corroborate detected visual objects with objects/actions mentioned in witness audio
        vision_objects = {
            str(item).strip().lower()
            for res in vision_results
            for item in res.get("evidence_facts", [])
        }
        audio_transcript_blob = " ".join(
            str(res.get("transcript", "")).lower() for res in audio_results
        )
        for obj in sorted(vision_objects):
            if obj and len(obj) > 2 and obj in audio_transcript_blob:
                consistency["matches"].append(
                    f"Visual object '{obj}' corroborated by witness audio testimony"
                )

        total_signals = len(consistency["matches"]) + len(consistency["conflicts"])
        if total_signals > 0:
            consistency["overall_score"] = round(len(consistency["matches"]) / total_signals, 2)
        elif all_sources:
            consistency["overall_score"] = 0.75

        return consistency

    def _add_uncertainty_markers(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign forensic certainty levels ('high', 'medium', 'low') from confidence scores
        and flag temporal uncertainty ('known' vs 'unknown').
        """
        for event in events:
            confidence = float(event.get("confidence", 0.5))
            if confidence >= 0.8:
                event["certainty"] = "high"
            elif confidence >= 0.6:
                event["certainty"] = "medium"
            else:
                event["certainty"] = "low"

            event["temporal_uncertainty"] = "known" if event.get("has_timestamp") else "unknown"
        return events

    def generate_scenarios(self, forensic_facts: Dict[str, Any]) -> List[str]:
        """Generate 3 grounded multimodal hypotheses from fused visual and auditory facts."""
        prompt = (
            "Analyze these fused visual and auditory forensic facts:\n"
            f"{json.dumps(forensic_facts, default=str)}\n"
            "Generate exactly 3 objective investigative hypotheses (do not accuse individuals):\n"
            "1. Primary Scenario (Most consistent across modalities)\n"
            "2. Alternative Scenario (Secondary / Non-criminal interpretation)\n"
            "3. Low-Probability Scenario (Discrepancy / Outlier explanation)\n"
            "Format: 3 concise bullet lines."
        )
        llm_res = generate_grounded_completion(prompt, temperature=0.1)
        if llm_res:
            lines = [ln.strip() for ln in llm_res.splitlines() if ln.strip()]
            if len(lines) >= 3:
                return lines[:3]

        matches = forensic_facts.get("consistency", {}).get("matches", [])
        conflicts = forensic_facts.get("consistency", {}).get("conflicts", [])
        corroboration_note = matches[0] if matches else "single-modality baseline observations"
        conflict_note = conflicts[0] if conflicts else "minor asynchronous timestamp offsets"

        return [
            f"1. Primary Scenario: Multimodal timeline aligns around {corroboration_note}, indicating a coordinated sequence captured across physical and testimonial records.",
            "2. Alternative Scenario: Visual detections and witness recollections reflect sequential but independent routine movements around the same premises.",
            f"3. Low-Probability / Audit Scenario: Account for {conflict_note} before drawing timeline conclusions; physical chain-of-custody verification is recommended.",
        ]

    def fuse_case(
        self,
        image_result: Optional[Dict[str, Any]] = None,
        audio_result: Optional[Dict[str, Any]] = None,
        video_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fuse available image, audio, and video findings into one unified forensic record."""
        unified_events: List[Dict[str, Any]] = []
        vision_list: List[Dict[str, Any]] = []
        audio_list: List[Dict[str, Any]] = []

        if image_result:
            vision_list.append(image_result)
            unified_events.append({
                "time": "00:00",
                "seconds": 0.0,
                "modality": "image",
                "event": image_result.get("visual_summary", "Static crime scene photograph analyzed"),
                "confidence": float(image_result.get("location_confidence", 0.85)),
                "has_timestamp": False,
            })

        if video_result:
            vision_list.append({
                "location": video_result.get("scene_intelligence", {}).get("location", ""),
                "evidence_facts": video_result.get("scene_intelligence", {}).get("objects_detected", []),
            })
            for item in video_result.get("timeline", []):
                unified_events.append({
                    "time": item.get("time", "00:00"),
                    "seconds": float(item.get("seconds", 0.0)),
                    "modality": "video",
                    "event": item.get("event", ""),
                    "confidence": float(item.get("confidence", 0.82)),
                    "has_timestamp": True,
                })

        if audio_result:
            audio_list.append(audio_result)
            for item in audio_result.get("timeline", []):
                unified_events.append({
                    "time": item.get("time", "00:00"),
                    "seconds": float(item.get("seconds", 0.0)),
                    "modality": "audio",
                    "event": f"Witness statement: {item.get('event', '')}",
                    "confidence": float(item.get("confidence", 0.78)),
                    "has_timestamp": True,
                })

        unified_events.sort(key=lambda e: (e["seconds"], e["modality"]))
        marked_events = self._add_uncertainty_markers(unified_events)
        consistency = self._check_consistency(vision_list, audio_list, [])

        fused_facts = {
            "consistency": consistency,
            "event_count": len(marked_events),
            "modalities_present": [
                m for m, r in (("image", image_result), ("audio", audio_result), ("video", video_result)) if r
            ],
        }
        hypotheses = self.generate_scenarios(fused_facts)

        return {
            "mode": "fusion",
            "modalities_fused": fused_facts["modalities_present"],
            "consistency": consistency,
            "unified_timeline": marked_events,
            "scenarios": hypotheses,
            "ethical_notice": (
                "Fused multimodal intelligence highlights corroborations and discrepancies across "
                "uploaded sources. Certainty markers reflect algorithmic confidence, not legal proof."
            ),
        }
