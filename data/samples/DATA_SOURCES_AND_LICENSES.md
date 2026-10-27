# Sample Datasets, Synthetic Media & Licensing Manifest

All demonstration files in `data/samples/` are **100% synthetic, deterministically generated assets** created specifically for the **CrimeVision AI** academic capstone project via `scripts/generate_samples.py`.

## Ethical & Legal Compliance
- **Zero Real Individuals**: No photographs, voices, or CCTV recordings of real individuals are used. Human figures are geometric silhouettes.
- **License**: Released under CC0 / MIT-compatible academic demonstration terms for unrestricted GitHub redistribution and classroom grading.

## Inventory of Generated Assets

| Modality | File Path | Specification | Intended Pipeline Demonstration |
| :--- | :--- | :--- | :--- |
| Image | `data/samples/images/synthetic_office_scene.jpg` | 1280x720 RGB JPEG | Staged office disturbance with desk, laptop, overturned chair, floor silhouette, knife prop, and numbered evidence markers (#1–#3) + 3D room projection. |
| Image | `data/samples/images/synthetic_retail_store_scene.jpg` | 1280x720 RGB JPEG | Staged retail store counter with display case, standing silhouette, handbag, and dropped necklace prop. |
| Audio | `data/samples/audio/synthetic_witness_store_robbery.wav` | 20.0s, 16kHz 16-bit Mono WAV + `.json` | Witness statement describing Maple Avenue retail store robbery, corroborated with `synthetic_retail_store_scene.jpg`, with English/Hindi/Telugu/French translations. |
| Audio | `data/samples/audio/synthetic_witness_office_burglary.wav` | 16.0s, 16kHz 16-bit Mono WAV + `.json` | Witness statement describing Suite 304 office crash, corroborated with `synthetic_office_scene.jpg`. |
| Video | `data/samples/videos/synthetic_store_cctv.mp4` | 10.0s, 640x360 @ 10fps H.264 MP4 | Surveillance sequence showing idle store (00:00–00:01), subject approaching counter (00:02–00:04), taking bag & rapid exit (00:05–00:09). |
| Video | `data/samples/videos/synthetic_corridor_cctv.mp4` | 8.0s, 640x360 @ 10fps H.264 MP4 | Routine corridor walkthrough demonstrating `NORMAL ACTIVITY` baseline classification. |
| Tabular | `data/samples/tabular/synthetic_forensic_benchmark.csv` | 5 Ground-Truth Cases (CSV) | Evaluates cross-modal consistency/conflict scoring, video crime classification, and Regex timestamp chat lookup via `scripts/run_evaluation.py`. |

## Regenerating Samples Locally

```bash
python3 scripts/generate_samples.py
```
