# Quantitative Evaluation Summary (Synthetic Forensic Benchmark)

Generated automatically by `python3 scripts/run_evaluation.py` against `data/samples/tabular/synthetic_forensic_benchmark.csv` and `data/samples/` media.

## Aggregate Algorithmic Validation Metrics

| Module / Subsystem | Benchmark Cases | Correct | Measured Accuracy |
| :--- | :---: | :---: | :---: |
| Cross-Modal Consistency & Conflict Audit (`FusionService`) | 5 | 5 | 100.0% |
| Surveillance Sequence Classification (`classify_crime`) | 5 | 5 | 100.0% |
| Temporal Chat Regex Extraction (`parse_time_from_question`) | 5 | 5 | 100.0% |

## End-to-End Sample Media Verification

- **Synthetic Office Scene (`synthetic_office_scene.jpg`)**: Skipped live vision inference (`skipped_unconfigured (Real image analysis requires either local RT-DETR/CLIP PyTorch weights or GEMINI_API_KEY for multimodal AI inference. Predefined/demo detections are disabled.)`).
- **Synthetic Store Robbery Audio (`synthetic_witness_store_robbery.wav`)**: 4 multilingual outputs verified (`english, hindi, telugu, french`) (1.39 ms).
- **Synthetic Store CCTV (`synthetic_store_cctv.mp4`)**: 10 frames extracted at 1Hz across 9.0s duration via FFmpeg (149.81 ms).
- **Forensic PDF Report (`outputs/reports/`)**: Valid `%PDF-1.4` generated (1928 bytes in 1.21 ms).

> **Note on Image Forensics**: Image Forensics uses real multimodal AI (`GEMINI_API_KEY`) or local neural checkpoints (`PekingU/rtdetr_r50vd`, `openai/clip-vit-base-patch32`, `Salesforce/blip-image-captioning-large`) and never returns predefined or hardcoded detections.
