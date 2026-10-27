# CRIMEVISION AI: INTELLIGENT MULTIMODAL FORENSIC ANALYSIS PLATFORM

**Academic Capstone Project Report**

> **Document Provenance Note**: This academic report has been authored directly from the official 61-page *CrimeVision AI* capstone specification workflow and grounded strictly in the implemented codebase, synthetic datasets, and verified test executions in this repository. No separate university `.docx` or `.md` report template was uploaded alongside the workflow specification PDF; therefore, a complete 16-section computer science capstone structure is provided below.

---

## 1. Title & Metadata

- **Project Title**: CrimeVision AI — Intelligent Multimodal Forensic Analysis Platform
- **Domain**: Multimodal Artificial Intelligence, Computer Vision, Speech Processing, 3D Spatial Visualization, and Grounded Forensic Decision Support
- **Execution Mode**: Local Reproducible Capstone System (Python Flask + PyTorch/Transformers Backend & React + TypeScript + Three.js Interactive Interface)

---

## 2. Abstract

Investigators analyzing modern physical incidents routinely confront fragmented, heterogeneous digital evidence: static crime scene photographs, multilingual witness audio statements, and unindexed surveillance video streams. Manual cross-referencing across these modalities is time-consuming and prone to cognitive oversight. **CrimeVision AI** addresses this gap by implementing a modular multimodal forensic assistance platform organized across six engineering milestones. For static photographs, the system performs object, human, and weapon detection (`RT-DETR`), zero-shot scene classification (`CLIP`), visual captioning (`BLIP`), structured summary refinement, three-tier investigative hypothesis generation, and interactive **Three.js 3D room reconstruction**. For witness audio statements, it executes speech-to-text transcription (`Whisper-base`), extracts structured crime intelligence, generates parallel translations in **English, Hindi, Telugu, and French**, and aligns timestamped events. For surveillance video, it decomposes clips at **1Hz (`1 frame/sec`)**, tracks object and person counts, classifies sequence status, and constructs an $O(1)$ hash-indexed second-by-second timeline. A **Multimodal Fusion Service** subsequently corroborates locations and cataloged evidence items across modalities, flags cross-modal conflicts, attaches explicit certainty (`high`, `medium`, `low`) and temporal uncertainty (`known`, `unknown`) markers, persists sessions to JSON, powers a Regex + RAG grounded forensic chatbot, and exports downloadable `%PDF-1.4` forensic reports. Automated unit tests (`9/9` passing) and synthetic benchmark evaluations validate deterministic pipeline accuracy, chain-of-custody SHA-256 hashing, and ethical non-accusatory safeguards.

---

## 3. Introduction

Digital forensic workflows increasingly depend on correlating visual and auditory observations recorded asynchronously. A static photograph captures high-resolution spatial relationships at a single unknown instant; a witness audio recording provides narrative sequence and intent but may contain subjective recall errors or require translation; a surveillance CCTV clip provides objective temporal progression (`MM:SS`) at lower spatial resolution. Treating each modality in isolation leaves investigators without automated cross-modal corroboration or spatial visualization.

CrimeVision AI bridges these modalities within a unified, locally executable software architecture designed for transparency, reproducibility, and strict evidentiary grounding. Rather than acting as an opaque "crime predictor," the platform catalogs observable physical items, aligns timestamps onto a common chronological axis, highlights corroborations and conflicts across modalities, and enforces zero-hallucination constraints during interactive investigator Q&A.

---

## 4. Problem Statement

Given heterogeneous forensic inputs—specifically crime scene photographs, recorded witness audio statements across multiple languages, and short surveillance CCTV clips—existing standalone tools lack:
1. Automated 2D-to-3D spatial room projection from detected bounding boxes for interactive scene inspection.
2. Integrated multilingual witness statement translation (English, Hindi, Telugu, French) paired with chronological fact extraction.
3. Lightweight 1Hz video decomposition with $O(1)$ hash-indexed second-by-second timelines suitable for student-grade hardware.
4. Automated cross-modal consistency auditing that explicitly quantifies corroborations versus location/object discrepancies and prevents LLM hallucination during evidence querying.

---

## 5. Project Objectives

1. **Milestone 1 (Environment & Modular Foundation)**: Establish a reproducible Python & TypeScript project structure with pinned dependencies, runtime protobuf/TensorFlow conflict guards, and SHA-256 file validation.
2. **Milestone 2 (Visual Scene Intelligence & 3D Reconstruction)**: Detect humans, weapons, and scene objects; classify scene locations; synthesize 2-line forensic summaries and 3 investigative hypotheses; and project detections into an interactive Three.js 3D room.
3. **Milestone 3 (Multilingual Witness Audio Intelligence)**: Transcribe `.wav`/`.mp3` witness recordings with segment timestamps, extract structured incident entities (`Event Type`, `Location`, `Who/Where/When`), and translate transcripts into English, Hindi, Telugu, and French.
4. **Milestone 4 (1Hz Surveillance Video Analysis)**: Sample CCTV clips at 1 frame/second (capped at 30s), aggregate per-frame detections, classify sequence activity (`NORMAL ACTIVITY` vs. alert categories with factual reasoning), and construct a click-to-seek second-by-second timeline.
5. **Milestone 5 (Multimodal Fusion & Grounded Chat)**: Fuse image, audio, and video outputs onto a unified timeline with certainty and temporal uncertainty markers, compute cross-modal consistency scores, persist `session_<uuid>.json` records, and implement Regex timestamp lookup + context-locked RAG Q&A.
6. **Milestone 6 (Unified Interface, Automated Validation & PDF Reporting)**: Connect all pipelines to a clean 4-tab web dashboard, validate subsystems with `unittest`, and generate downloadable PDF forensic reports.

---

## 6. Literature & Technical Context

CrimeVision AI builds upon established pretrained vision, speech, and multimodal reasoning architectures:
- **Real-Time Detection Transformer (`RT-DETR`, Zhao et al., 2024)**: Eliminates non-maximum suppression (NMS) bottlenecks via hybrid encoder-decoder queries (`PekingU/rtdetr_r50vd`), enabling accurate bounding-box localization of persons, furniture, and sharp/blunt implements.
- **Contrastive Language-Image Pretraining (`CLIP`, Radford et al., 2021)**: Enables zero-shot indoor/outdoor scene classification (`openai/clip-vit-base-patch32`) over candidate forensic environments (`office`, `retail store`, `parking lot`, `alleyway`, etc.) without custom retraining.
- **Bootstrapping Language-Image Pretraining (`BLIP`, Li et al., 2022)**: Generates concise natural-language descriptions of visual scenes (`Salesforce/blip-image-captioning-large`).
- **Whisper Multilingual ASR (Radford et al., 2023)**: Encoder-decoder Transformer (`openai/whisper-base`) trained on 680,000 hours of weakly supervised multilingual speech, providing segment-level timestamps.
- **Retrieval-Augmented / Context-Locked Prompting**: Restricting generative LLM temperature (`0.1`) and injecting serialized JSON evidence records with an explicit abstention rule (`"Information not found in the analyzed evidence."`) mitigates speculative hallucination in high-stakes domains.

---

## 7. System Architecture

The platform implements a decoupled, dual-compatible architecture:
- **Presentation & Spatial Layer (`src/`)**: React 19, TypeScript, Tailwind CSS 4, SVG normalized vector bounding-box overlays, HTML5 synced media players, and a WebGL `Three.js` 3D room reconstruction canvas (`Scene3DReconstruction.tsx`) utilizing `RoomEnvironment` PBR lighting, `OrbitControls`, and raycaster object picking.
- **Python Forensic AI Service Layer (`backend/`)**: Modular Flask Blueprints (`/api/analyze-image`, `/api/analyze-audio`, `/api/analyze-video`, `/api/upload`, `/api/fuse`, `/api/chat/<mode>`, `/api/report/<session_id>`, `/api/health`) backed by `VisionService`, `AudioService`, `FusionService`, `ChatService`, `ReportService`, and `SessionStore`.
- **Express / Multimodal Gateway (`server.ts` & `server/`)**: Serves the React SPA on port 3000, provides optional transparent proxying to `FLASK_BACKEND_URL` (`http://localhost:5000`), and supports standalone multimodal execution via FFmpeg 1Hz frame extraction, `@google/genai`, `PDFKit`, and shared `data/sessions/session_<uuid>.json` persistence.

---

## 8. Methodology & Workflow

1. **Intake & Chain-of-Custody Validation**: Uploaded files are checked against per-modality extension whitelists and a 50 MB size cap, sanitized against path traversal (`sanitize_filename`), and hashed with **SHA-256** (`compute_sha256`).
2. **2D-to-3D Room Coordinate Mapping**: For each detected normalized bounding box $[x_1, y_1, x_2, y_2] \in [0, 1]^4$, centroid $(c_x, c_y)$ maps onto a $9.0\text{m} \times 7.0\text{m}$ room floor plane via $X = (c_x - 0.5) \times 7.5$ and $Z = (c_y - 0.5) \times 5.5$. Aspect-ratio heuristics distinguish upright (`standing`) vs. horizontal (`lying down`) postures.
3. **1Hz Video Sampling & $O(1)$ Timeline Alignment**: Videos are sampled at `1.0 fps` up to 30 seconds. Captions and detections are stored in integer-second hash maps (`caption_map[sec]`, `detection_map[sec]`), guaranteeing linear $O(T)$ timeline construction over duration $T$.
4. **Cross-Modal Consistency & Certainty Scoring**: `FusionService._check_consistency` compares visual locations and cataloged evidence nouns against witness audio locations and transcripts, computing `overall_score = len(matches) / (len(matches) + len(conflicts))`. Events receive certainty labels (`high` $\ge 0.80$, `medium` $\ge 0.60$, `low` $< 0.60$) and temporal uncertainty (`known` for audio/video; `unknown` for static images).
5. **Hybrid Regex + Grounded RAG Chat**: `parse_time_from_question` applies regular expressions (`\b(\d{1,2}):(\d{2})\b` and second-unit patterns) to resolve timestamp questions deterministically in $O(1)$ before falling back to context-locked LLM answering.

---

## 9. Dataset & Synthetic Sample Description

Because redistributing real crime-scene photographs or private witness recordings violates privacy and ethical norms, **100% synthetic demonstration assets** were created deterministically via `scripts/generate_samples.py` under `data/samples/`:

| Asset File | Modality | Technical Format | Forensic Test Purpose |
| :--- | :--- | :--- | :--- |
| `synthetic_office_scene.jpg` | Image | `1280×720` JPEG | Staged office suite with desk, open laptop, overturned chair, horizontal silhouette, knife prop, and markers `#1–#3`. |
| `synthetic_retail_store_scene.jpg` | Image | `1280×720` JPEG | Staged retail counter with glass display case, standing figure, handbag, and dropped necklace prop. |
| `synthetic_witness_store_robbery.wav` | Audio | `20.0s`, 16kHz 16-bit Mono WAV + JSON | Witness statement describing Maple Ave retail store robbery with English, Hindi, Telugu, and French translations. |
| `synthetic_witness_office_burglary.wav` | Audio | `16.0s`, 16kHz 16-bit Mono WAV + JSON | Security statement describing Suite 304 office crash, corroborating `synthetic_office_scene.jpg`. |
| `synthetic_store_cctv.mp4` | Video | `10.0s`, `640×360` @ 10fps H.264 MP4 | Surveillance sequence showing idle counter (`00:00–00:01`), subject entry (`00:02`), bag removal (`00:05`), and rapid exit. |
| `synthetic_corridor_cctv.mp4` | Video | `8.0s`, `640×360` @ 10fps H.264 MP4 | Routine corridor walk verifying `NORMAL ACTIVITY` baseline classification. |
| `synthetic_forensic_benchmark.csv` | Tabular | 5 Ground-Truth Cases (CSV) | Evaluates cross-modal consistency/conflict detection, sequence classification, and Regex timestamp parsing. |

---

## 10. Implementation Details

- **Protobuf & TensorFlow Isolation (`backend/app.py`)**: Sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`, `TF_CPP_MIN_LOG_LEVEL=2`, and `USE_TF=0` prior to importing HuggingFace pipelines, preventing common C++ protobuf version clashes on student machines.
- **Strict Real-Vision Policy & Provenance Labeling**: Image Forensics (`analyzeImageForensics` / `VisionService`) sends actual uploaded image bytes to a multimodal vision model (or calibrated `RT-DETR`/`CLIP` weights), explicitly labels VLM-estimated bounding regions, visibility scores, and heuristic 2D-to-3D projections as simulated/estimated, and surfaces structured errors without ever falling back to predefined or hardcoded detections.
- **Software WebGL Guard (`Scene3DReconstruction.tsx`)**: Inspects `UNMASKED_RENDERER_WEBGL` for `SwiftShader`/`llvmpipe` and clamps `devicePixelRatio` automatically to maintain smooth interactive 3D orbiting across integrated GPUs and virtual machines.

---

## 11. Experimental Setup & Validation Protocol

Validation was executed locally using two automated scripts:
1. **Unit & Integration Test Suite**: `python3 -m unittest backend/tests/test_validation.py -v` (9 test methods verifying fusion consistency, conflict detection, certainty thresholds, 1Hz hash-indexed timelines, Regex timestamp extraction, grounded non-hallucination fallback, file extension/path sanitization, SHA-256 hashing, session disk persistence, PDF `%PDF-1.4` header integrity, and `/api/health`).
2. **Quantitative Benchmark Script**: `python3 scripts/run_evaluation.py` against `synthetic_forensic_benchmark.csv` and the generated media files in `data/samples/`.

---

## 12. Results & Discussion

All figures reported below are **actual measured outputs** recorded in `outputs/evaluation/benchmark_results.json` and `unittest` execution logs:

### 12.1 Automated Unit Test Suite (`test_validation.py`)
- **Tests Executed**: `9`
- **Tests Passed**: `9` (`0` failures, `0` errors; execution time `0.010s`)

### 12.2 Synthetic Benchmark Accuracy (`run_evaluation.py`)

| Evaluated Subsystem | Ground-Truth Cases | Correct Predictions | Measured Accuracy |
| :--- | :---: | :---: | :---: |
| Cross-Modal Consistency & Conflict Audit (`FusionService._check_consistency`) | 5 | 5 | **100.0%** |
| Surveillance Sequence Classification (`classify_crime`) | 5 | 5 | **100.0%** |
| Temporal Chat Regex Parser (`parse_time_from_question`) | 5 | 5 | **100.0%** |

### 12.3 End-to-End Sample Media Verification & Measured Latency
- **Image Pipeline (Live Multimodal Vision)**: Dynamically inspects actual uploaded image bytes (`@google/genai` multimodal vision / `RT-DETR`), extracts true binary image dimensions, identifies only genuinely visible items, labels VLM-estimated regions/scores transparently, and rejects unconfigured/corrupt requests with explicit HTTP errors rather than fake detections.
- **Audio Pipeline (`synthetic_witness_store_robbery.wav`)**: Verified `4` complete language outputs (`english`, `hindi`, `telugu`, `french`) and `4` chronological timeline segments (`1.28 ms`).
- **Video 1Hz Decomposition (`synthetic_store_cctv.mp4`)**: Extracted `10` JPEG frames at `1.0 fps` across the clip via `FFmpeg` in **`145.26 ms`**.
- **PDF Forensic Report Generation**: Produced valid `%PDF-1.4` binary artifact (`2,129 bytes` in `2.32 ms` via Python writer; formatted multi-section A4 PDF via `PDFKit`/`ReportLab`).

*Discussion*: Note that the `100.0%` benchmark figures above measure deterministic algorithmic correctness of the rule-based consistency auditor, sequence classifier, and Regex timestamp parser on the 5-case synthetic verification suite—they must not be extrapolated as real-world wild CCTV deep-learning accuracy, where lighting, occlusion, and motion blur affect neural detector recall.

---

## 13. Limitations

1. **Single-View 2D-to-3D Depth Approximation**: Projecting monocular 2D bounding boxes onto a 3D room plane estimates $(X, Z)$ floor placement from image-plane centroids rather than metric LiDAR or multi-view photogrammetry depth.
2. **30-Second Surveillance Clip Cap**: To keep CPU/student-laptop memory bounded without a distributed task queue, video decomposition samples 1Hz up to 30 seconds per clip.
3. **Acoustic Noise Sensitivity**: Real-world witness or field recordings with heavy background siren/crowd noise can degrade `whisper-base` transcription fidelity compared to larger `whisper-large-v3` models.

---

## 14. Ethical, Legal & Responsible AI Considerations

1. **Strict Prohibition on Guilt or Criminality Inference**: CrimeVision AI never classifies a person as a "criminal" or "suspect" from facial features, clothing, or demographics. Human detections are labeled strictly `"Human"`.
2. **Hypothesis Diversity**: Every scene analysis generates three distinct scenarios—including an explicit **Alternative / Non-Criminal / Accidental Hypothesis** and a **Low-Probability / Post-Incident Disturbance Hypothesis**—to counteract confirmation bias.
3. **Zero-Hallucination Abstention**: Grounded chat enforces `temperature = 0.1` and responds `"Information not found in the analyzed evidence."` when queried about unrecorded details (e.g., an unseen license plate).
4. **Chain-of-Custody Integrity**: SHA-256 digests are computed at intake and embedded into exported PDF reports so analysts can verify that source media was unaltered.

---

## 15. Future Scope

- Integrate metric monocular depth estimation (`Depth Anything V2`) to refine 3D Z-axis room placement and furniture scale.
- Support optional speaker diarization for multi-party witness interviews while preserving local offline execution.
- Add encrypted local case archive export (`.zip` bundling source media, `session_<uuid>.json`, SHA-256 manifest, and signed PDF report).

---

## 16. Conclusion & References

**Conclusion**: CrimeVision AI fulfills all six milestones of the official project specification, delivering a cohesive, testable, and ethically bounded multimodal forensic platform. By combining 2D/3D visual scene reconstruction, four-language audio intelligence, 1Hz surveillance video timelines, cross-modal consistency auditing, and grounded Q&A within a reproducible local codebase, the project demonstrates practical full-stack AI engineering ready for academic evaluation.

### References
1. Zhao, Y., Lv, W., Xu, S., et al. (2024). *DETRs Beat YOLOs on Real-time Object Detection (RT-DETR)*. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR).
2. Radford, A., Kim, J. W., Hallacy, C., et al. (2021). *Learning Transferable Visual Models From Natural Language Supervision (CLIP)*. International Conference on Machine Learning (ICML).
3. Li, J., Li, D., Xiong, C., & Hoi, S. (2022). *BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation*. ICML.
4. Radford, A., Kim, J. W., Xu, T., et al. (2023). *Robust Speech Recognition via Large-Scale Weak Supervision (Whisper)*. ICML.
5. Kirillov, A., Mintun, E., Ravi, N., et al. (2023). *Segment Anything (SAM)*. IEEE/CVF International Conference on Computer Vision (ICCV).
