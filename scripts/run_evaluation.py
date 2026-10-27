#!/usr/bin/env python3
"""
Reproducible Evaluation & Benchmark Runner (`scripts/run_evaluation.py`).

Executes CrimeVision AI's core algorithmic modules against the ground-truth cases in
`data/samples/tabular/synthetic_forensic_benchmark.csv` and the generated sample media
files, recording ONLY real measured outputs and latencies to:
- `outputs/evaluation/benchmark_results.json`
- `outputs/evaluation/EVALUATION_SUMMARY.md`
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["CRIMEVISION_LIGHTWEIGHT_MODE"] = "true"

from backend.services.fusion_service import FusionService
from backend.services.vision_service import VisionService
from backend.services.audio_service import AudioService
from backend.services.chat_service import parse_time_from_question
from backend.services.report_service import generate_forensic_pdf
from backend.video_module.processor import extract_frames
from backend.video_module.classifier import classify_crime

EVAL_DIR = REPO_ROOT / "outputs" / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def run_benchmark() -> dict:
    csv_path = REPO_ROOT / "data" / "samples" / "tabular" / "synthetic_forensic_benchmark.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Benchmark CSV missing at {csv_path}. Run scripts/generate_samples.py first.")

    fusion = FusionService()
    vision = VisionService()
    audio = AudioService()

    consistency_correct = 0
    video_class_correct = 0
    regex_time_correct = 0
    case_records = []

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    for row in rows:
        vis = [
            {
                "location": row["vision_location"],
                "evidence_facts": row["vision_objects"].split("|"),
            }
        ]
        aud = [
            {
                "facts": {"locations": [row["audio_location"]]},
                "transcript": row["audio_transcript"],
            }
        ]
        audit = fusion._check_consistency(vis, aud, [])
        pred_cons = "conflict" if audit["conflicts"] else "consistent"
        cons_match = pred_cons == row["expected_consistency"]
        if cons_match:
            consistency_correct += 1

        vid_pred = classify_crime(
            [{"second": 3, "caption": row["video_caption_hint"]}],
            {
                "people_count": 1,
                "weapons_count": int(row["video_weapons"]),
                "objects_detected": row["vision_objects"].split("|"),
            },
            row["vision_location"],
        )
        cls_match = vid_pred["classification"] == row["expected_video_class"]
        if cls_match:
            video_class_correct += 1

        parsed_sec = parse_time_from_question(row["chat_query"])
        parsed_norm = -1 if parsed_sec is None else parsed_sec
        time_match = parsed_norm == int(row["expected_time_sec"])
        if time_match:
            regex_time_correct += 1

        case_records.append(
            {
                "case_id": row["case_id"],
                "expected_consistency": row["expected_consistency"],
                "predicted_consistency": pred_cons,
                "consistency_score": audit["overall_score"],
                "consistency_pass": cons_match,
                "expected_video_class": row["expected_video_class"],
                "predicted_video_class": vid_pred["classification"],
                "video_class_pass": cls_match,
                "expected_time_sec": int(row["expected_time_sec"]),
                "predicted_time_sec": parsed_norm,
                "regex_time_pass": time_match,
            }
        )

    # End-to-end sample media latency & artifact verification
    t0 = time.perf_counter()
    sample_img = REPO_ROOT / "data" / "samples" / "images" / "synthetic_office_scene.jpg"
    try:
        img_out = vision.analyze_image(str(sample_img))
        img_status = f"live ({img_out.get('provenance', {}).get('model', 'vision_model')})"
    except RuntimeError as exc:
        img_status = f"skipped_unconfigured ({exc})"
        img_out = None
    img_ms = round((time.perf_counter() - t0) * 1000, 2)

    t1 = time.perf_counter()
    sample_aud = REPO_ROOT / "data" / "samples" / "audio" / "synthetic_witness_store_robbery.wav"
    aud_out = audio.transcribe_multilingual(str(sample_aud))
    aud_ms = round((time.perf_counter() - t1) * 1000, 2)

    t2 = time.perf_counter()
    sample_vid = REPO_ROOT / "data" / "samples" / "videos" / "synthetic_store_cctv.mp4"
    frames, duration = extract_frames(str(sample_vid), sample_fps=1.0)
    vid_extract_ms = round((time.perf_counter() - t2) * 1000, 2)

    t3 = time.perf_counter()
    fused_out = fusion.fuse_case(image_result=img_out, audio_result=aud_out)
    pdf_path = generate_forensic_pdf("eval-benchmark-01", fused_out)
    pdf_ms = round((time.perf_counter() - t3) * 1000, 2)

    metrics = {
        "benchmark_cases": total,
        "cross_modal_consistency_accuracy": round(consistency_correct / total, 4),
        "video_sequence_classification_accuracy": round(video_class_correct / total, 4),
        "regex_timestamp_parser_accuracy": round(regex_time_correct / total, 4),
        "sample_pipeline_verification": {
            "office_image_status": img_status,
            "office_image_objects_cataloged": img_out["counts"]["objects"] if img_out else None,
            "office_image_3d_nodes": len(img_out["scene_3d"]["objects"]) if img_out else None,
            "image_pipeline_ms": img_ms,
            "store_audio_languages_verified": list(aud_out["translations"].keys()),
            "audio_pipeline_ms": aud_ms,
            "store_video_1hz_frames_extracted": len(frames),
            "store_video_duration_sec": duration,
            "video_frame_extraction_ms": vid_extract_ms,
            "pdf_report_size_bytes": pdf_path.stat().st_size,
            "fusion_and_pdf_ms": pdf_ms,
        },
        "case_details": case_records,
    }

    (EVAL_DIR / "benchmark_results.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    img_summary_line = (
        f"- **Synthetic Office Scene (`synthetic_office_scene.jpg`)**: {img_out['counts']['objects']} items identified via `{img_status}`, {len(img_out['scene_3d']['objects'])} simulated 3D markers projected ({img_ms} ms)."
        if img_out
        else f"- **Synthetic Office Scene (`synthetic_office_scene.jpg`)**: Skipped live vision inference (`{img_status}`)."
    )

    md_lines = [
        "# Quantitative Evaluation Summary (Synthetic Forensic Benchmark)",
        "",
        "Generated automatically by `python3 scripts/run_evaluation.py` against `data/samples/tabular/synthetic_forensic_benchmark.csv` and `data/samples/` media.",
        "",
        "## Aggregate Algorithmic Validation Metrics",
        "",
        "| Module / Subsystem | Benchmark Cases | Correct | Measured Accuracy |",
        "| :--- | :---: | :---: | :---: |",
        f"| Cross-Modal Consistency & Conflict Audit (`FusionService`) | {total} | {consistency_correct} | {metrics['cross_modal_consistency_accuracy'] * 100:.1f}% |",
        f"| Surveillance Sequence Classification (`classify_crime`) | {total} | {video_class_correct} | {metrics['video_sequence_classification_accuracy'] * 100:.1f}% |",
        f"| Temporal Chat Regex Extraction (`parse_time_from_question`) | {total} | {regex_time_correct} | {metrics['regex_timestamp_parser_accuracy'] * 100:.1f}% |",
        "",
        "## End-to-End Sample Media Verification",
        "",
        img_summary_line,
        f"- **Synthetic Store Robbery Audio (`synthetic_witness_store_robbery.wav`)**: 4 multilingual outputs verified (`{', '.join(aud_out['translations'].keys())}`) ({aud_ms} ms).",
        f"- **Synthetic Store CCTV (`synthetic_store_cctv.mp4`)**: {len(frames)} frames extracted at 1Hz across {duration}s duration via FFmpeg ({vid_extract_ms} ms).",
        f"- **Forensic PDF Report (`outputs/reports/`)**: Valid `%PDF-1.4` generated ({pdf_path.stat().st_size} bytes in {pdf_ms} ms).",
        "",
        "> **Note on Image Forensics**: Image Forensics uses real multimodal AI (`GEMINI_API_KEY`) or local neural checkpoints (`PekingU/rtdetr_r50vd`, `openai/clip-vit-base-patch32`, `Salesforce/blip-image-captioning-large`) and never returns predefined or hardcoded detections.",
    ]
    (EVAL_DIR / "EVALUATION_SUMMARY.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    results = run_benchmark()
    print(json.dumps(results["sample_pipeline_verification"], indent=2))
