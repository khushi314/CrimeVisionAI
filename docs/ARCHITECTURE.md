# CrimeVision AI — Technical Architecture & System Design

## 1. Architectural Overview

CrimeVision AI employs a modular, service-oriented multimodal pipeline separating **evidence intake & chain-of-custody validation**, **modality-specific perception (Image, Audio, Video)**, **cross-modal temporal fusion**, **session-grounded RAG question answering**, and **interactive 2D/3D spatial visualization**.

```
+-----------------------------------------------------------------------------------+
|                        React 19 + TypeScript + Tailwind UI                        |
|  +-----------------+ +------------------+ +------------------+ +----------------+ |
|  | Image Forensics | | Audio Intel      | | Video CCTV (1Hz) | | Multimodal     | |
|  | + SVG BBoxes    | | + EN/HI/TE/FR    | | + Click-to-Seek  | | Fusion Audit   | |
|  | + Three.js 3D   | | + Audio Player   | | + Crime Class    | | + Certainty    | |
|  +--------+--------+ +--------+---------+ +--------+---------+ +--------+-------+ |
|           +-------------------+--------------------+--------------------+         |
|                               | REST JSON / Multipart (/api/*)                    |
+-------------------------------|---------------------------------------------------+
                                v
+-----------------------------------------------------------------------------------+
|                API Gateway & Forensic Orchestration Layer                         |
|  - Standalone Mode: Express + FFmpeg + Gemini Multimodal (`server.ts`, port 3000) |
|  - Python ML Mode:  Flask Blueprints (`backend/app.py`, port 5000 via proxy)      |
+-----------------------------------------------------------------------------------+
       |                        |                        |                   |
       v                        v                        v                   v
+--------------+        +---------------+        +---------------+   +--------------+
| Vision       |        | Audio         |        | Video 1Hz     |   | Fusion, Chat |
| Service      |        | Service       |        | Pipeline      |   | & PDF Report |
| - RT-DETR    |        | - Whisper ASR |        | - OpenCV /    |   | - Consistency|
| - CLIP       |        | - Crime Facts |        |   FFmpeg 1fps |   | - Certainty  |
| - BLIP       |        | - EN/HI/TE/FR |        | - Hash-Index  |   | - Regex O(1) |
| - 3D Map     |        | - Timeline    |        |   Timeline    |   | - ReportLab  |
+--------------+        +---------------+        +---------------+   +--------------+
                                        |
                                        v
                   +-----------------------------------------+
                   | Disk-Backed Session & Artifact Storage  |
                   | - data/sessions/session_<uuid>.json     |
                   | - outputs/reports/report_<uuid>.pdf     |
                   +-----------------------------------------+
```

---

## 2. Core Algorithmic Workflows

### 2.1 Image Forensics & 2D-to-3D Spatial Projection (`Milestone 2`)
1. **Object & Weapon Detection (`RT-DETR` / `PekingU/rtdetr_r50vd`)**: Extracts bounding boxes $[x_1, y_1, x_2, y_2]$ filtered at confidence $\ge 0.45$, mapping classes into `person` (`Human`), `weapon` (`knife`, `gun`, `scissors`, `baseball bat`), and physical `object` (`desk`, `laptop`, `chair`, `display case`, `handbag`, `necklace`).
2. **Zero-Shot Environment Classification (`CLIP` / `openai/clip-vit-base-patch32`)**: Computes cosine similarity probabilities over candidate indoor/outdoor prompts (`"a surveillance or forensic photo of a {location}"`).
3. **2D-to-3D Room Plane Projection**: Normalized bounding-box centers $(c_x, c_y) \in [0, 1]^2$ are projected onto a $9.0\text{m} \times 7.0\text{m}$ Three.js forensic room coordinate frame:
   $$X_{\text{world}} = (c_x - 0.5) \times 7.5, \qquad Z_{\text{world}} = (c_y - 0.5) \times 5.5$$
   Aspect ratios $(x_2 - x_1) > 1.18 \times (y_2 - y_1)$ automatically orient human silhouettes horizontally on the floor plane; upright bounding boxes render standing figures alongside numbered yellow pyramidal evidence markers.

### 2.2 Multilingual Witness Audio Pipeline (`Milestone 3`)
1. **ASR Transcription (`openai/whisper-base`)**: Decodes `.wav`/`.mp3`/`.m4a`/`.ogg`/`.flac` witness recordings with chunk-level timestamps `(start_raw, end_raw)` guarded by a 120-second execution timeout.
2. **Multilingual Translation**: Generates parallel transcripts in **English**, **Hindi (Devanagari)**, **Telugu**, and **French** so investigators across linguistic jurisdictions can inspect witness statements without altering the original transcript.

### 2.3 1Hz Video Decomposition & Hash-Indexed Timeline (`Milestone 4`)
1. **1Hz Frame Sampling**: `extract_frames` samples exactly 1 frame per integer second up to `max_video_duration_seconds = 30` using OpenCV (`cv2.VideoCapture`) or `ffmpeg -vf fps=1`.
2. **O(1) Hash-Indexed Timeline (`build_timeline`)**: Asynchronous frame captions and per-frame object detections are indexed into `caption_map[sec]` and `detection_map[sec]`, producing an exact chronological sequence `00:00 .. MM:SS` without drift or quadratic timestamp matching.

### 2.4 Cross-Modal Consistency Audit & Certainty Markers (`Milestone 5`)
1. **Consistency Score (`FusionService._check_consistency`)**:
   - Compares normalized spatial locations across visual (`CLIP`) and auditory (`Whisper + Entity Extraction`) records, supporting substring equivalence (e.g., `"store"` $\leftrightarrow$ `"retail store"`).
   - Cross-checks cataloged visual evidence items (`handbag`, `necklace`, `knife`, `laptop`) against the witness audio transcript.
   - Computes:
     $$\text{Consistency Score} = \frac{|\text{Matches}|}{|\text{Matches}| + |\text{Conflicts}|}$$
2. **Forensic Certainty Markers (`_add_uncertainty_markers`)**:
   - `confidence >= 0.80` $\rightarrow$ `certainty = "high"`
   - `0.60 <= confidence < 0.80` $\rightarrow$ `certainty = "medium"`
   - `confidence < 0.60` $\rightarrow$ `certainty = "low"`
   - Static photographs carry `temporal_uncertainty = "unknown"`, whereas timestamped audio/video streams carry `temporal_uncertainty = "known"`.
3. **Deterministic Regex Timestamp Lookup + Grounded Chat (`ChatService`)**:
   - `parse_time_from_question` intercepts explicit timestamp queries (`"What happened at 00:05?"`, `"at 12 seconds"`) via regular expressions for deterministic `O(1)` timeline lookup.
   - General questions execute context-locked RAG (`temperature = 0.1`) with an explicit anti-hallucination rule returning `"Information not found in the analyzed evidence."` whenever queried facts are absent from `session_<uuid>.json`.
