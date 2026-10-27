"""
Vision Service — Real Image Forensics via Local Neural Vision (RT-DETR + CLIP + BLIP)
or Multimodal Vision API (Gemini Multimodal REST), 3D Coordinate Projection, and
Scenario Hypothesis Generation (Milestone 2: Activities 2.1 & 2.2).

Zero Predefined/Demo Detections Policy:
Never inserts predefined object labels, bounding boxes, confidence scores, or locations.
If neither local neural weights nor a multimodal vision API key is available, raises a
descriptive RuntimeError instead of fabricating fake detections.
"""

import base64
import json
import mimetypes
import os
import struct
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from backend.config import MODEL_CONFIG
    from backend.utils.logger import setup_logger
    from backend.utils.model_loader import (
        load_rt_detr_model,
        load_clip_model,
        load_blip2_model,
        load_sam_model,
    )
    from backend.utils.groq_utils import generate_grounded_completion
except ImportError:
    from config import MODEL_CONFIG
    from utils.logger import setup_logger
    from utils.model_loader import (
        load_rt_detr_model,
        load_clip_model,
        load_blip2_model,
        load_sam_model,
    )
    from utils.groq_utils import generate_grounded_completion

logger = setup_logger("vision_service")

ETHICAL_NOTICE = (
    "Automated forensic assistance output. Detections and scenario hypotheses "
    "require verification by qualified investigators and are not proof of criminal conduct."
)

GEMINI_MULTIMODAL_MODELS = (
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
)


class VisionService:
    """Service for computer vision forensic image analysis and 3D scene projection."""

    def __init__(self) -> None:
        self.rt_detr: Optional[Dict[str, Any]] = None
        self.clip: Optional[Dict[str, Any]] = None
        self.blip2: Optional[Dict[str, Any]] = None
        self.sam: Optional[Any] = None

    def _ensure_models_loaded(self) -> None:
        """Lazily load RT-DETR, CLIP, BLIP, and optional SAM models."""
        if self.rt_detr is None:
            self.rt_detr = load_rt_detr_model()
        if self.clip is None:
            self.clip = load_clip_model()
        if self.blip2 is None:
            self.blip2 = load_blip2_model()
        if self.sam is None:
            self.sam = load_sam_model()

    def detect_objects(self, image_path: str, confidence_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Detect objects, persons, and potential weapons in an image using calibrated RT-DETR.
        Raises RuntimeError if RT-DETR weights are not loaded (never fabricates detections).
        """
        path_obj = Path(image_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        self._ensure_models_loaded()
        if self.rt_detr is None:
            raise RuntimeError(
                "Local RT-DETR object detector is not loaded in this environment. "
                "Use VisionService.analyze_image() with GEMINI_API_KEY configured or install PyTorch + Transformers weights."
            )

        threshold = confidence_threshold or MODEL_CONFIG["rt_detr"]["confidence_threshold"]
        weapon_labels = MODEL_CONFIG["rt_detr"]["weapon_labels"]
        person_labels = MODEL_CONFIG["rt_detr"]["person_labels"]

        import torch
        from PIL import Image

        image = Image.open(path_obj).convert("RGB")
        width, height = image.size
        processor = self.rt_detr["processor"]
        model = self.rt_detr["model"]
        device = self.rt_detr["device"]

        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]]).to(device)
        results = processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=threshold
        )[0]

        detections: List[Dict[str, Any]] = []
        for score, label_id, box in zip(results["scores"], results["labels"], results["boxes"]):
            raw_label = model.config.id2label[int(label_id)].lower()
            mapped_label = "Human" if raw_label in person_labels else raw_label
            category = (
                "weapon"
                if raw_label in weapon_labels
                else "person"
                if raw_label in person_labels
                else "object"
            )
            coords = [round(float(v), 2) for v in box.tolist()]
            detections.append({
                "label": mapped_label,
                "raw_label": raw_label,
                "category": category,
                "confidence": round(float(score), 3),
                "bbox": coords,
                "normalized_bbox": [
                    round(coords[0] / max(width, 1), 4),
                    round(coords[1] / max(height, 1), 4),
                    round(coords[2] / max(width, 1), 4),
                    round(coords[3] / max(height, 1), 4),
                ],
                "bbox_simulated": False,
                "confidence_simulated": False,
            })

        persons_count = sum(1 for d in detections if d["category"] == "person")
        weapons_count = sum(1 for d in detections if d["category"] == "weapon")

        return {
            "image_width": width,
            "image_height": height,
            "detections": detections,
            "counts": {
                "objects": len(detections),
                "persons": persons_count,
                "weapons": weapons_count,
            },
        }

    def classify_location(self, image_path: str) -> Dict[str, Any]:
        """Classify spatial environment via zero-shot CLIP."""
        self._ensure_models_loaded()
        if self.clip is None:
            raise RuntimeError("Local CLIP scene classifier is not loaded.")

        candidates = MODEL_CONFIG["clip"]["candidate_locations"]
        import torch
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        prompts = [f"a surveillance or forensic photo of a {loc}" for loc in candidates]
        processor = self.clip["processor"]
        model = self.clip["model"]
        device = self.clip["device"]

        inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0]
            best_idx = int(torch.argmax(probs).item())
            return {
                "location": candidates[best_idx],
                "confidence": round(float(probs[best_idx].item()), 3),
            }

    def generate_caption(self, image_path: str, detections: List[Dict[str, Any]], location: str) -> str:
        """Generate natural-language visual summary using BLIP or detected object facts."""
        self._ensure_models_loaded()
        if self.blip2 is not None:
            import torch
            from PIL import Image

            image = Image.open(image_path).convert("RGB")
            processor = self.blip2["processor"]
            model = self.blip2["model"]
            device = self.blip2["device"]

            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=MODEL_CONFIG["blip2"]["max_new_tokens"])
            caption = processor.decode(out[0], skip_special_tokens=True).strip()
            if caption:
                return caption

        labels = [d["label"] for d in detections]
        unique_labels = list(dict.fromkeys(labels))
        items_str = ", ".join(unique_labels[:8]) if unique_labels else "no foreground objects detected"
        return f"Visual inspection of {location}; observed items: {items_str}."

    def refine_caption(self, raw_caption: str, location: str, counts: Dict[str, int]) -> Dict[str, str]:
        """Refine raw visual caption into the 2-line structured AI Scene Summary."""
        prompt = (
            "Refine the following raw image caption into a professional forensic summary.\n\n"
            "STRUCTURE:\n"
            "Line 1: Summary Type: [Brief Category: e.g., Indoor Scene Inspection / Outdoor Photograph]\n"
            "Line 2: Brief Description: [Concise objective description of the scene without assuming guilt]\n\n"
            f"Location: {location}\n"
            f"Counts: {counts}\n"
            f"Raw Caption: {raw_caption}\n\n"
            "Return ONLY the refined two-line summary."
        )
        llm_text = generate_grounded_completion(prompt, temperature=0.1)
        if llm_text and "Brief Description:" in llm_text:
            lines = [ln.strip() for ln in llm_text.splitlines() if ln.strip()]
            summary_type = lines[0].replace("Summary Type:", "").strip() if lines else "Visual Scene Inspection"
            brief_desc = (
                lines[1].replace("Brief Description:", "").strip()
                if len(lines) > 1
                else raw_caption
            )
            return {"summary_type": summary_type, "brief_description": brief_desc}

        summary_type = (
            "High-Priority Physical Evidence Scene"
            if counts.get("weapons", 0) > 0
            else "Visual Scene Inspection"
        )
        brief_desc = (
            f"Objective visual inspection of {location}: {raw_caption} "
            f"(Persons observed: {counts.get('persons', 0)}, Items cataloged: {counts.get('objects', 0)})."
        )
        return {"summary_type": summary_type, "brief_description": brief_desc}

    def generate_scenarios(self, forensic_facts: Dict[str, Any]) -> List[Dict[str, str]]:
        """Synthesize 3 distinct, non-accusatory hypotheses grounded strictly in observed scene items."""
        prompt = (
            "Analyze these objective visual observations:\n"
            f"{forensic_facts}\n"
            "Generate exactly 3 hypotheses grounded ONLY in observed items (never accuse an identifiable person):\n"
            "1. Primary Scene Interpretation\n"
            "2. Alternative Contextual Explanation\n"
            "3. Verification & Evidentiary Considerations\n"
            "Return 3 numbered lines."
        )
        llm_text = generate_grounded_completion(prompt, temperature=0.15)
        if llm_text:
            parsed = [ln.strip() for ln in llm_text.splitlines() if ln.strip() and ln.strip()[0] in "123"]
            if len(parsed) >= 3:
                titles = [
                    "Scenario 1 — Primary Scene Interpretation",
                    "Scenario 2 — Alternative Contextual Explanation",
                    "Scenario 3 — Verification & Evidentiary Considerations",
                ]
                return [
                    {"title": titles[idx], "description": parsed[idx].lstrip("123. )-")}
                    for idx in range(3)
                ]

        loc = forensic_facts.get("location", "observed environment")
        has_weapon = forensic_facts.get("counts", {}).get("weapons", 0) > 0
        items_list = forensic_facts.get("evidence_facts", [])
        items = ", ".join(items_list[:5]) if items_list else "no distinct foreground items"

        if has_weapon:
            return [
                {
                    "title": "Scenario 1 — Primary Scene Interpretation",
                    "description": f"Potential security-relevant incident within the {loc} involving observed items ({items}); physical chain-of-custody verification required.",
                },
                {
                    "title": "Scenario 2 — Alternative Contextual Explanation",
                    "description": f"Observed items ({items}) in the {loc} may reflect routine tool usage, training props, or accidental displacement without criminal activity.",
                },
                {
                    "title": "Scenario 3 — Verification & Evidentiary Considerations",
                    "description": f"Independent corroboration of timestamps, lighting, and physical context in the {loc} is required prior to drawing conclusions.",
                },
            ]

        return [
            {
                "title": "Scenario 1 — Primary Scene Interpretation",
                "description": f"Everyday or baseline scene state within the {loc} featuring {items}, with zero weapon-class items detected.",
            },
            {
                "title": "Scenario 2 — Alternative Contextual Explanation",
                "description": f"Static photographic capture of {loc} prior to or independent of any reported disturbance.",
            },
            {
                "title": "Scenario 3 — Verification & Evidentiary Considerations",
                "description": f"Cross-reference image metadata and corroborating witness or video records if {loc} is linked to an active inquiry.",
            },
        ]

    def project_3d_scene(
        self,
        detections: List[Dict[str, Any]],
        location: str,
        width: int,
        height: int,
        simulated: bool = True,
    ) -> Dict[str, Any]:
        """Project 2D normalized bounding boxes into a simulated 3D floor-plane coordinate system."""
        objects_3d: List[Dict[str, Any]] = []
        valid_dets = [
            det for det in detections
            if isinstance(det.get("normalized_bbox"), list) and len(det["normalized_bbox"]) == 4
        ]
        for idx, det in enumerate(valid_dets):
            nx1, ny1, nx2, ny2 = det["normalized_bbox"]
            cx = (nx1 + nx2) / 2.0
            cy = (ny1 + ny2) / 2.0
            box_h = max(0.08, ny2 - ny1)

            world_x = round((cx - 0.5) * 7.5, 2)
            world_z = round((cy - 0.5) * 5.5, 2)
            elevation = 0.0 if det["category"] in ("person", "object") else 0.08

            objects_3d.append({
                "id": f"ev_{idx + 1}",
                "marker_number": idx + 1,
                "label": det["label"],
                "category": det["category"],
                "confidence": det.get("confidence"),
                "position": {"x": world_x, "y": elevation, "z": world_z},
                "scale": round(max(0.55, min(1.55, box_h * 2.2)), 2),
                "bbox": det["normalized_bbox"],
                "simulated_projection": True,
            })

        return {
            "room_type": location,
            "dimensions": {"width": 9.0, "height": 3.2, "depth": 7.0},
            "objects": objects_3d,
            "is_simulated": simulated,
        }

    def _analyze_with_gemini_multimodal(self, path_obj: Path) -> Dict[str, Any]:
        """Analyze actual uploaded image bytes via Gemini Multimodal REST API when local PyTorch models are absent."""
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "MY_GEMINI_API_KEY":
            raise RuntimeError(
                "Real image analysis requires either local RT-DETR/CLIP PyTorch weights or GEMINI_API_KEY "
                "for multimodal AI inference. Predefined/demo detections are disabled."
            )

        raw_bytes = path_obj.read_bytes()
        mime_type, width, height = self._inspect_image_bytes(raw_bytes, path_obj)
        b64_data = base64.b64encode(raw_bytes).decode("ascii")

        prompt = (
            "Inspect the actual visual contents of this uploaded image objectively.\n"
            "Report ONLY objects, humans, potential weapons, and scene details genuinely visible in THIS image.\n"
            "NEVER invent knives, weapons, laptops, desks, chairs, or people if they are not visible.\n"
            "Return strict JSON with keys: location (string), estimated_location_confidence (number 0..1), "
            "summary_type (string), brief_description (string), visual_summary (string), "
            "actions_detected (array of strings), detections (array of {label, category ('person'|'weapon'|'object'), "
            "estimated_confidence (0..1), box_2d ([ymin, xmin, ymax, xmax] in 0..1000), observation_note}), "
            "and scenarios (array of 3 {title, description})."
        )

        payload_body = json.dumps({
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                    {"text": prompt},
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }).encode("utf-8")

        last_err: Optional[Exception] = None
        raw_text: Optional[str] = None
        model_used = GEMINI_MULTIMODAL_MODELS[0]

        for attempt in range(2):
            for model_name in GEMINI_MULTIMODAL_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                req = urllib.request.Request(
                    url,
                    data=payload_body,
                    headers={"Content-Type": "application/json", "User-Agent": "aistudio-build"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        resp_json = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_json.get("candidates") or []
                    parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
                    text_candidate = "".join(p.get("text", "") for p in parts).strip()
                    if text_candidate:
                        raw_text = text_candidate
                        model_used = model_name
                        break
                except urllib.error.HTTPError as http_err:
                    last_err = http_err
                    if http_err.code in (429, 500, 502, 503, 504):
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    raise RuntimeError(f"Multimodal API HTTP {http_err.code}: {http_err.reason}") from http_err
                except Exception as exc:
                    last_err = exc
                    time.sleep(1.0 * (attempt + 1))
            if raw_text:
                break

        if not raw_text:
            raise RuntimeError(f"Multimodal vision inference failed: {last_err}")

        parsed_raw = json.loads(raw_text)
        parsed = parsed_raw[0] if isinstance(parsed_raw, list) and parsed_raw else parsed_raw

        detections: List[Dict[str, Any]] = []
        for d in parsed.get("detections") or []:
            if not isinstance(d, dict) or not str(d.get("label", "")).strip():
                continue
            cat = str(d.get("category", "object")).lower().strip()
            if cat not in ("person", "weapon", "object"):
                cat = "object"
            raw_label = str(d["label"]).strip()
            nbbox = self._parse_box_2d(d.get("box_2d"))
            pixel_bbox = (
                [
                    round(nbbox[0] * width),
                    round(nbbox[1] * height),
                    round(nbbox[2] * width),
                    round(nbbox[3] * height),
                ]
                if nbbox
                else None
            )
            conf_raw = d.get("estimated_confidence")
            conf = (
                round(float(conf_raw), 3)
                if isinstance(conf_raw, (int, float)) and 0 < float(conf_raw) <= 1.0
                else None
            )
            detections.append({
                "label": "Human" if cat == "person" else raw_label,
                "raw_label": raw_label.lower(),
                "category": cat,
                "confidence": conf,
                "bbox": pixel_bbox,
                "normalized_bbox": nbbox,
                "bbox_simulated": nbbox is not None,
                "confidence_simulated": conf is not None,
                "observation_note": str(d.get("observation_note", "")).strip() or None,
            })

        persons = sum(1 for d in detections if d["category"] == "person")
        weapons = sum(1 for d in detections if d["category"] == "weapon")
        counts = {"objects": len(detections), "persons": persons, "weapons": weapons}
        location = str(parsed.get("location") or "unclassified scene").strip()
        loc_conf_raw = parsed.get("estimated_location_confidence")
        loc_conf = (
            round(float(loc_conf_raw), 3)
            if isinstance(loc_conf_raw, (int, float)) and 0 < float(loc_conf_raw) <= 1.0
            else None
        )
        evidence_facts = list(dict.fromkeys(
            f"{d['label']} ({d['observation_note']})" if d.get("observation_note") else d["label"]
            for d in detections
        ))
        actions = [str(a).strip() for a in (parsed.get("actions_detected") or []) if str(a).strip()] or [
            "No active motion or distinct human posture observed"
        ]
        scenarios = [
            {"title": str(s.get("title", "")).strip(), "description": str(s.get("description", "")).strip()}
            for s in (parsed.get("scenarios") or [])[:3]
            if isinstance(s, dict) and s.get("title") and s.get("description")
        ]
        if not scenarios:
            scenarios = self.generate_scenarios({
                "location": location,
                "counts": counts,
                "evidence_facts": evidence_facts,
            })

        has_bbox = any(d["normalized_bbox"] is not None for d in detections)
        has_conf = any(d["confidence"] is not None for d in detections)

        return {
            "mode": "image",
            "ai_scene_summary": {
                "summary_type": str(parsed.get("summary_type") or "Visual Scene Inspection").strip(),
                "brief_description": str(
                    parsed.get("brief_description") or parsed.get("visual_summary") or "Visual inspection completed."
                ).strip(),
            },
            "visual_summary": str(parsed.get("visual_summary") or parsed.get("brief_description") or "").strip(),
            "counts": counts,
            "location": location,
            "location_confidence": loc_conf,
            "actions_detected": actions,
            "evidence_facts": evidence_facts,
            "detections": detections,
            "scenarios": scenarios,
            "scene_3d": self.project_3d_scene(detections, location, width, height, simulated=True),
            "provenance": {
                "model": model_used,
                "analysis_mode": "multimodal_vision_vlm",
                "bbox_source": "vlm_estimated" if has_bbox else "unavailable",
                "confidence_source": "vlm_estimated" if has_conf else "unavailable",
                "spatial_3d_source": "simulated_from_2d" if has_bbox else "unavailable",
                "image_dimensions": {"width": width, "height": height},
                "disclaimer": (
                    "Object labels, approximate bounding boxes, visibility scores, and 3D floor-plane positions "
                    "are estimated dynamically from the uploaded image by a multimodal vision-language model "
                    "rather than a calibrated pixel-level object detector."
                ),
            },
            "ethical_notice": ETHICAL_NOTICE,
        }

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Execute full image forensic analysis pipeline using real vision models only."""
        path_obj = Path(image_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        self._ensure_models_loaded()
        if self.rt_detr is None or self.clip is None:
            return self._analyze_with_gemini_multimodal(path_obj)

        det_result = self.detect_objects(image_path)
        detections = det_result["detections"]
        counts = det_result["counts"]
        loc_info = self.classify_location(image_path)
        location = loc_info["location"]

        raw_caption = self.generate_caption(image_path, detections, location)
        refined = self.refine_caption(raw_caption, location, counts)
        evidence_facts = list(dict.fromkeys(d["label"] for d in detections))
        actions_detected = self._infer_posture_or_state(detections, raw_caption)

        forensic_facts = {
            "location": location,
            "counts": counts,
            "evidence_facts": evidence_facts,
            "actions_detected": actions_detected,
            "visual_summary": raw_caption,
        }
        scenarios = self.generate_scenarios(forensic_facts)
        scene_3d = self.project_3d_scene(
            detections, location, det_result["image_width"], det_result["image_height"], simulated=True
        )

        return {
            "mode": "image",
            "ai_scene_summary": refined,
            "visual_summary": raw_caption,
            "counts": counts,
            "location": location,
            "location_confidence": loc_info["confidence"],
            "actions_detected": actions_detected,
            "evidence_facts": evidence_facts,
            "detections": detections,
            "scenarios": scenarios,
            "scene_3d": scene_3d,
            "provenance": {
                "model": MODEL_CONFIG["rt_detr"]["model_id"],
                "analysis_mode": "calibrated_detector",
                "bbox_source": "detector_calibrated",
                "confidence_source": "detector_calibrated",
                "spatial_3d_source": "simulated_from_2d",
                "image_dimensions": {
                    "width": det_result["image_width"],
                    "height": det_result["image_height"],
                },
                "disclaimer": (
                    "2D detections produced by calibrated RT-DETR; 3D room placement is a simulated "
                    "heuristic floor-plane projection."
                ),
            },
            "ethical_notice": ETHICAL_NOTICE,
        }

    @staticmethod
    def _parse_box_2d(raw_box: Any) -> Optional[List[float]]:
        if not isinstance(raw_box, list) or len(raw_box) != 4:
            return None
        try:
            nums = [float(v) for v in raw_box]
        except (TypeError, ValueError):
            return None
        scale = 1.0 if all(0.0 <= n <= 1.05 for n in nums) and any(0.0 < n < 1.0 for n in nums) else 1000.0
        ymin = max(0.0, min(1.0, nums[0] / scale))
        xmin = max(0.0, min(1.0, nums[1] / scale))
        ymax = max(0.0, min(1.0, nums[2] / scale))
        xmax = max(0.0, min(1.0, nums[3] / scale))
        if xmax < xmin:
            xmin, xmax = xmax, xmin
        if ymax < ymin:
            ymin, ymax = ymax, ymin
        if (xmax - xmin) < 0.008 or (ymax - ymin) < 0.008:
            return None
        return [round(xmin, 4), round(ymin, 4), round(xmax, 4), round(ymax, 4)]

    @staticmethod
    def _infer_posture_or_state(detections: List[Dict[str, Any]], caption: str) -> List[str]:
        actions: List[str] = []
        lower_cap = caption.lower()
        if "lying" in lower_cap or "floor" in lower_cap:
            actions.append("horizontal posture / floor-level subject")
        for det in detections:
            nb = det.get("normalized_bbox")
            if det["category"] == "person" and isinstance(nb, list) and len(nb) == 4:
                nx1, ny1, nx2, ny2 = nb
                if (nx2 - nx1) > (ny2 - ny1) * 1.15:
                    actions.append("lying down")
                else:
                    actions.append("standing / upright presence")
            elif det["category"] == "weapon":
                actions.append(f"proximally placed {det['label']} detected")
        return list(dict.fromkeys(actions)) or ["static scene / no active motion"]

    @staticmethod
    def _inspect_image_bytes(raw: bytes, path_obj: Path) -> Tuple[str, int, int]:
        if len(raw) < 16:
            raise ValueError(f"Uploaded file '{path_obj.name}' is empty or truncated.")
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(raw)) as img:
                fmt = (img.format or "JPEG").lower()
                mime = f"image/{'jpeg' if fmt == 'jpg' else fmt}"
                return (mime, img.size[0], img.size[1])
        except Exception:
            pass

        if raw[:8] == b"\x89PNG\r\n\x1a\n" and len(raw) >= 24:
            w, h = struct.unpack(">II", raw[16:24])
            return ("image/png", int(w), int(h))
        if raw[:3] == b"\xff\xd8\xff":
            return ("image/jpeg", 1000, 1000)
        if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            return ("image/webp", 1000, 1000)
        if raw[:2] == b"BM" and len(raw) >= 26:
            w, h = struct.unpack("<ii", raw[18:26])
            return ("image/bmp", abs(int(w)), abs(int(h)))
        guessed, _ = mimetypes.guess_type(path_obj.name)
        if guessed and guessed.startswith("image/"):
            return (guessed, 1000, 1000)
        raise ValueError(f"File '{path_obj.name}' is not a valid image.")
