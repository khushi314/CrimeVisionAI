"""
Automated Validation & Unit Test Suite (`backend/tests/test_validation.py`).

Covers Milestone 6 Activity 6.2 & Academic Testing Requirements:
1. Cross-modal consistency & conflict detection (`FusionService._check_consistency`).
2. Forensic certainty & temporal uncertainty markers (`FusionService._add_uncertainty_markers`).
3. O(1) hash-indexed video timeline construction & idle gap consolidation (`build_timeline`).
4. Regex timestamp lookup & grounded non-hallucinatory chat (`parse_time_from_question`, `query_chat`).
5. File extension validation, sanitization, and SHA-256 chain-of-custody hashing.
6. Persistent JSON session store CRUD (`SessionStore`).
7. End-to-end Vision, Audio, and PDF Report generation (`%PDF-1.4` verification).
8. Backend API health check (`/api/health` via Flask `test_client()` when Flask is installed,
   plus direct payload contract verification).

Run locally with:
    python3 -m unittest backend/tests/test_validation.py -v
"""

import os
import sys
import tempfile
import unittest
import wave
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["CRIMEVISION_LIGHTWEIGHT_MODE"] = "true"

from backend.app import get_health_payload
from backend.services.fusion_service import FusionService
from backend.services.session_store import SessionStore, session_store
from backend.services.chat_service import parse_time_from_question, get_event_at_time, query_chat
from backend.services.vision_service import VisionService
from backend.services.audio_service import AudioService
from backend.services.report_service import generate_forensic_pdf
from backend.video_module.timeline import build_timeline
from backend.video_module.classifier import classify_crime
from backend.utils.file_handler import validate_upload_extension, sanitize_filename, compute_sha256


class TestCrimeVisionValidation(unittest.TestCase):
    """Comprehensive unit and integration validation tests for CrimeVision AI."""

    def setUp(self) -> None:
        self.fusion = FusionService()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_fusion_logic_consistency(self) -> None:
        """Verify cross-modal corroboration matches and conflict flags across vision & audio."""
        vision_match = [{"location": "retail store", "evidence_facts": ["handbag", "necklace"]}]
        audio_match = [
            {
                "facts": {"locations": ["store"]},
                "transcript": "Two individuals ran out of the store carrying a dark handbag and dropped a necklace.",
            }
        ]
        consistent = self.fusion._check_consistency(vision_match, audio_match, [])
        self.assertGreaterEqual(consistent["overall_score"], 0.9)
        self.assertEqual(len(consistent["conflicts"]), 0)
        self.assertGreaterEqual(len(consistent["matches"]), 2)

        # Conflict case: Office image vs Parking Lot audio statement
        vision_conflict = [{"location": "office", "evidence_facts": ["laptop"]}]
        audio_conflict = [
            {
                "facts": {"locations": ["alleyway"]},
                "transcript": "I heard shouting in the alleyway behind the street.",
            }
        ]
        conflicted = self.fusion._check_consistency(vision_conflict, audio_conflict, [])
        self.assertEqual(len(conflicted["conflicts"]), 1)
        self.assertEqual(conflicted["overall_score"], 0.0)

    def test_uncertainty_markers(self) -> None:
        """Verify high/medium/low certainty thresholds and temporal uncertainty flags."""
        raw_events = [
            {"time": "00:00", "seconds": 0.0, "confidence": 0.91, "has_timestamp": True},
            {"time": "00:05", "seconds": 5.0, "confidence": 0.68, "has_timestamp": True},
            {"time": "00:00", "seconds": 0.0, "confidence": 0.42, "has_timestamp": False},
        ]
        marked = self.fusion._add_uncertainty_markers(raw_events)
        self.assertEqual(marked[0]["certainty"], "high")
        self.assertEqual(marked[0]["temporal_uncertainty"], "known")
        self.assertEqual(marked[1]["certainty"], "medium")
        self.assertEqual(marked[2]["certainty"], "low")
        self.assertEqual(marked[2]["temporal_uncertainty"], "unknown")

    def test_timeline_hash_indexing_and_gap_consolidation(self) -> None:
        """Verify O(1) second-indexed 1Hz timeline construction and idle frame filling."""
        captions = [
            {"timestamp": 0, "caption": " Retail store entrance clear. "},
            {"timestamp": 1, "caption": "Person enters frame near counter."},
            {"timestamp": 5, "caption": "Person exits rapidly toward door."},
        ]
        detections = [
            {"timestamp": 0, "persons_count": 0, "weapons_count": 0, "detections": []},
            {
                "timestamp": 1,
                "persons_count": 1,
                "weapons_count": 0,
                "detections": [{"label": "Human", "confidence": 0.89}],
            },
            {
                "timestamp": 5,
                "persons_count": 1,
                "weapons_count": 1,
                "detections": [{"label": "knife", "confidence": 0.84}],
            },
        ]
        bundle = build_timeline(captions, detections, duration=6.0)
        timeline = bundle["timeline"]
        self.assertEqual(len(timeline), 7)  # 00:00 through 00:06 inclusive at 1Hz
        idle_entries = [t for t in timeline if t["event"] == "No significant activity"]
        self.assertEqual(len(idle_entries), 4)  # seconds 2, 3, 4, 6
        sec5 = [t for t in timeline if int(t["seconds"]) == 5][0]
        self.assertEqual(sec5["severity"], "alert")

    def test_chat_regex_time_lookup_and_grounded_rag(self) -> None:
        """Verify Regex timestamp extraction and non-hallucinatory fallback."""
        self.assertEqual(parse_time_from_question("What happened at 00:05?"), 5)
        self.assertEqual(parse_time_from_question("Describe activity at 1:12 in the clip"), 72)
        self.assertEqual(parse_time_from_question("Was anyone visible at 8 seconds?"), 8)
        self.assertIsNone(parse_time_from_question("What objects were detected in the room?"))

        sid = session_store.create_session(
            {
                "mode": "video",
                "location": "retail store",
                "visual_summary": "Surveillance clip of a retail store counter.",
                "scene_intelligence": {
                    "objects_detected": ["Human", "handbag"],
                    "people_count": 1,
                    "location": "retail store",
                },
                "timeline": [
                    {"time": "00:00", "seconds": 0, "event": "Store interior quiet."},
                    {"time": "00:05", "seconds": 5, "event": "Subject grabs handbag near counter."},
                ],
            }
        )
        try:
            ans_time = query_chat(sid, "What happened at 00:05?", mode="video")
            self.assertIn("handbag", ans_time)

            ans_missing = query_chat(sid, "What is the license plate number of the helicopter?", mode="video")
            self.assertIn("Information not found", ans_missing)
        finally:
            test_file = REPO_ROOT / "data" / "sessions" / f"session_{sid}.json"
            if test_file.exists():
                test_file.unlink()
            session_store._store.pop(sid, None)

    def test_file_validation_and_sha256(self) -> None:
        """Verify extension whitelist, empty filename rejection, path traversal sanitization, and SHA-256."""
        ok_img, _ = validate_upload_extension("crime_scene_01.jpg", "image")
        self.assertTrue(ok_img)

        bad_ext, msg = validate_upload_extension("malware.exe", "image")
        self.assertFalse(bad_ext)
        self.assertIn("Unsupported", msg)

        empty_ok, _ = validate_upload_extension("", "audio")
        self.assertFalse(empty_ok)

        clean_name = sanitize_filename("../../etc/passwd;drop.mp4")
        self.assertNotIn("..", clean_name)
        self.assertNotIn("/", clean_name)

        sample_file = self.temp_path / "evidence.bin"
        sample_file.write_bytes(b"crimevision-forensic-payload")
        digest = compute_sha256(sample_file)
        self.assertEqual(len(digest), 64)

    def test_session_persistence(self) -> None:
        """Verify SessionStore writes and reloads `session_<id>.json` accurately."""
        local_store = SessionStore(sessions_dir=self.temp_path)
        sid = local_store.create_session({"mode": "image", "location": "office"})
        loaded = local_store.get_session(sid)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["location"], "office")
        self.assertEqual(len(local_store.list_sessions()), 1)

    def test_vision_audio_and_pdf_report_pipeline(self) -> None:
        """Verify VisionService rejects unconfigured fake fallbacks, parses multimodal JSON dynamically, and generates valid PDF 1.4."""
        from unittest.mock import patch, MagicMock
        import json as _json

        img_path = self.temp_path / "outdoor_bicycle.png"
        img_path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10"
            b"\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x0cIDATx\x9cc`\xf8\xcf"
            b"\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        vision = VisionService()

        # 1. Verify NO hardcoded fallback detections are returned when GEMINI_API_KEY is absent
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                vision.analyze_image(str(img_path))

        # 2. Verify dynamic multimodal parsing reflects the actual model response (never Human/knife/laptop/desk/chair)
        mock_vlm_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": _json.dumps(
                                    {
                                        "location": "outdoor park path",
                                        "estimated_location_confidence": 0.93,
                                        "summary_type": "Benign Outdoor Scene Inspection",
                                        "brief_description": "A red bicycle parked beside a wooden park bench on a paved walkway.",
                                        "visual_summary": "Daylight photograph of an outdoor park path containing a parked red bicycle and wooden bench.",
                                        "actions_detected": ["Static scene — no human subjects visible"],
                                        "detections": [
                                            {
                                                "label": "bicycle",
                                                "category": "object",
                                                "estimated_confidence": 0.94,
                                                "box_2d": [320, 180, 790, 610],
                                                "observation_note": "parked upright beside bench",
                                            },
                                            {
                                                "label": "park bench",
                                                "category": "object",
                                                "estimated_confidence": 0.91,
                                                "box_2d": [410, 580, 740, 910],
                                                "observation_note": "wooden slats intact",
                                            },
                                        ],
                                        "scenarios": [
                                            {"title": "Scenario 1", "description": "Routine recreational stop along park walkway."},
                                            {"title": "Scenario 2", "description": "Unattended bicycle left temporarily near seating area."},
                                            {"title": "Scenario 3", "description": "Baseline reference photo with zero threat indicators."},
                                        ],
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        mock_http_resp = MagicMock()
        mock_http_resp.read.return_value = _json.dumps(mock_vlm_payload).encode("utf-8")
        mock_http_resp.__enter__.return_value = mock_http_resp

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_valid_api_key_for_unit_spec"}, clear=False):
            with patch("urllib.request.urlopen", return_value=mock_http_resp):
                img_res = vision.analyze_image(str(img_path))

        self.assertEqual(img_res["mode"], "image")
        self.assertEqual(img_res["location"], "outdoor park path")
        self.assertEqual(img_res["counts"]["persons"], 0)
        self.assertEqual(img_res["counts"]["weapons"], 0)
        self.assertEqual([d["label"] for d in img_res["detections"]], ["bicycle", "park bench"])
        self.assertTrue(img_res["detections"][0]["bbox_simulated"])
        self.assertEqual(img_res["provenance"]["bbox_source"], "vlm_estimated")
        self.assertEqual(len(img_res["scenarios"]), 3)
        self.assertEqual(len(img_res["scene_3d"]["objects"]), 2)

        wav_path = self.temp_path / "witness_statement.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(struct.pack("<" + "h" * 8000, *([0] * 8000)))

        audio = AudioService()
        aud_res = audio.transcribe_multilingual(str(wav_path))
        self.assertEqual(aud_res["mode"], "audio")
        for lang in ("english", "hindi", "telugu", "french"):
            self.assertIn(lang, aud_res["translations"])
            self.assertTrue(len(aud_res["translations"][lang]) > 0)

        fused = self.fusion.fuse_case(image_result=img_res, audio_result=aud_res)
        self.assertIn("consistency", fused)
        pdf_path = generate_forensic_pdf("testsession1234", img_res)
        try:
            self.assertTrue(pdf_path.exists())
            header = pdf_path.read_bytes()[:8]
            self.assertTrue(header.startswith(b"%PDF-1."))
        finally:
            if pdf_path.exists():
                pdf_path.unlink()

    def test_video_crime_classifier(self) -> None:
        """Verify video sequence classifier distinguishes routine vs alert sequences."""
        normal_res = classify_crime(
            [{"second": 0, "caption": "Person walking calmly past storefront."}],
            {"people_count": 1, "weapons_count": 0, "objects_detected": ["Human"]},
            "retail store",
        )
        self.assertEqual(normal_res["classification"], "NORMAL ACTIVITY")

        alert_res = classify_crime(
            [{"second": 3, "caption": "Individual holding knife near counter."}],
            {"people_count": 2, "weapons_count": 1, "objects_detected": ["Human", "knife"]},
            "retail store",
        )
        self.assertEqual(alert_res["classification"], "POTENTIAL WEAPON / SAFETY ALERT")

    def test_api_health(self) -> None:
        """Verify health payload structure and Flask `/api/health` route if Flask is installed."""
        payload = get_health_payload()
        self.assertEqual(payload["status"], "healthy")
        self.assertIn("modules", payload)

        try:
            from backend.app import create_app

            app = create_app()
            client = app.test_client()
            resp = client.get("/api/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data["status"], "healthy")
        except ImportError:
            # Flask is listed in requirements.txt for local student venv; verified via payload contract here
            pass


if __name__ == "__main__":
    unittest.main()
