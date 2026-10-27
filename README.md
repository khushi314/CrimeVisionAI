# CrimeVision AI — Intelligent Multimodal Forensic Analysis Platform

**CrimeVision AI** is an academic capstone platform for **objective, multimodal forensic scene assistance**. It unifies computer vision scene inspection, interactive Three.js 3D spatial reconstruction, multilingual witness statement transcription (English, Hindi, Telugu, French), 1Hz surveillance CCTV decomposition, cross-modal consistency auditing, session-grounded RAG question answering, and downloadable PDF forensic reports.

> **Scope & Deployment Notice**: This repository is engineered for **local execution, automated testing, reproducible benchmarking, and academic GitHub submission**. No paid cloud hosting or external deployment configuration is required.

---

## Key Capabilities (Mapped to Official Milestones 1–6)

1. **Image Forensics & Interactive 3D Scene Reconstruction (`Milestone 2`)**
   - Detects humans, potential weapons (`knife`, `gun`, `scissors`, `bat`), and physical scene objects (`RT-DETR` / multimodal vision) with normalized 2D bounding boxes and SHA-256 chain-of-custody hashing.
   - Classifies indoor/outdoor scene location (`CLIP` zero-shot spatial prompts), refines a structured 2-line `AI Scene Summary`, and generates **3 distinct, non-accusatory investigative scenario hypotheses**.
   - Projects normalized 2D detections onto a calibrated $9.0\text{m} \times 7.0\text{m}$ **Three.js 3D Room Reconstruction** with posture-aware silhouettes, furniture geometry, numbered yellow pyramidal evidence markers (`#1..#N`), raycaster click inspection, and camera presets.
2. **Multilingual Witness Audio Intelligence (`Milestone 3`)**
   - Transcribes `.wav`, `.mp3`, `.m4a`, `.ogg`, and `.flac` witness recordings (`openai/whisper-base` / multimodal ASR) with segment timestamps and a 120-second timeout guard.
   - Produces an `AI Intelligence Report` (`Event Type`, `Location`, `Who/Where/When` facts), interactive **English, Hindi (हिन्दी), Telugu (తెలుగు), and French (Français)** translations, and a click-to-seek `MM:SS` statement timeline.
3. **1Hz Surveillance Video Decomposition (`Milestone 4`)**
   - Samples CCTV footage (`.mp4`, `.webm`, `.mov`, `.avi`, `.mkv`) at **1 frame per second (1Hz)** up to 30 seconds via OpenCV / FFmpeg.
   - Aggregates people and weapon counts, classifies sequence status (`NORMAL ACTIVITY`, `SUSPICIOUS RAPID MOVEMENT`, `POTENTIAL WEAPON / SAFETY ALERT`) with an explicit factual reason, and builds an **O(1) hash-indexed second-by-second timeline** synced to video playback.
4. **Multimodal Fusion & Certainty Scoring (`Milestone 5`)**
   - Audits cross-modal consistency (`FusionService._check_consistency`) across analyzed Image, Audio, and Video sessions, computing an overall consistency score (`%`), listing corroborated matches, and flagging spatial discrepancies.
   - Attaches algorithmic certainty markers (`high` $\ge 0.80$, `medium` $\ge 0.60$, `low` $< 0.60$) and temporal uncertainty (`known` vs `unknown`) to a unified chronological timeline persisted in `data/sessions/session_<uuid>.json`.
5. **Grounded Forensic Q&A & PDF Reporting (`Milestone 5 & 6`)**
   - Intercepts explicit timestamp queries (`"What happened at 00:05?"`, `"at 12 seconds"`) via regular expressions (`parse_time_from_question`) for deterministic `O(1)` lookup, and answers general queries using strictly grounded RAG (`temperature=0.1`, returning `"Information not found in the analyzed evidence."` when facts are absent).
   - Exports formatted `%PDF-1.4` **Forensic Intelligence Reports** (`/api/report/<session_id>`) containing SHA-256 digests, cataloged observations, consistency audits, timelines, hypotheses, and ethical disclaimers.

---

## Repository Structure

```text
crime-vision-ai/
├── backend/                        # Official Python Flask + PyTorch/HuggingFace AI Backend
│   ├── app.py                      # Flask factory, Milestone 1 env guards & /api/health
│   ├── config.py                   # Centralized model IDs, thresholds, and directory paths
│   ├── requirements.txt            # Pinned Python dependencies (PyTorch, Transformers, Flask...)
│   ├── audio_module/               # Whisper ASR, crime fact extraction, 4-language translations
│   ├── video_module/               # 1Hz OpenCV/FFmpeg sampler, detector, classifier & timeline
│   ├── routes/                     # Upload, processing, session results, PDF report & chat routes
│   ├── services/                   # VisionService, AudioService, FusionService, ChatService, SessionStore
│   ├── utils/                      # Model loader, Groq client wrapper, SHA-256 file validator, logger
│   └── tests/
│       └── test_validation.py      # Automated unit & integration validation suite (9 test cases)
├── server/                         # Node/Express gateway & Gemini/FFmpeg multimodal engine
│   ├── geminiForensicEngine.ts     # Server-side multimodal vision, audio, 1Hz video, fusion & PDFKit
│   └── sessionStore.ts             # Interchangeable disk-backed session_<uuid>.json persistence
├── src/                            # React 19 + TypeScript + Tailwind CSS + Three.js Frontend
│   ├── App.tsx                     # 3-zone forensic dashboard shell & session history drawer
│   ├── components/
│   │   ├── Scene3DReconstruction.tsx # Interactive Three.js WebGL 3D crime scene room
│   │   ├── ImageAnalysisView.tsx   # Milestone 2 workspace (2D SVG bboxes + 3D room + scenarios)
│   │   ├── AudioAnalysisView.tsx   # Milestone 3 workspace (EN/HI/TE/FR tabs + audio timeline)
│   │   ├── VideoAnalysisView.tsx   # Milestone 4 workspace (1Hz CCTV player + click-to-seek timeline)
│   │   ├── MultimodalFusionView.tsx# Milestone 5 workspace (consistency audit + certainty markers)
│   │   └── ForensicChatPanel.tsx   # Context-locked RAG & Regex timestamp Q&A panel
│   ├── services/api.ts             # Typed REST API client
│   └── types/forensic.ts           # Domain TypeScript interfaces
├── scripts/
│   ├── generate_samples.py         # Deterministic generator for synthetic images, WAVs, MP4s & CSV
│   └── run_evaluation.py           # Reproducible benchmark evaluator writing measured JSON/MD metrics
├── data/
│   ├── samples/                    # Redistribution-safe synthetic forensic demo media & CSV benchmark
│   ├── sessions/                   # Runtime persisted session_<uuid>.json records (git-ignored)
│   └── uploads/                    # Runtime uploaded evidence files (git-ignored)
├── outputs/
│   ├── evaluation/                 # Measured benchmark_results.json & EVALUATION_SUMMARY.md
│   └── reports/                    # Generated downloadable PDF forensic reports (git-ignored)
├── docs/
│   ├── ARCHITECTURE.md             # System architecture, 3D math & timeline algorithms
│   ├── REQUIREMENT_CHECKLIST.md    # Traceability matrix for Milestones 1–6
│   └── GITHUB_UPLOAD_GUIDE.md      # Git initialization & clean GitHub upload instructions
├── PROJECT_REPORT.md               # Complete 16-section academic capstone project report
├── server.ts                       # Full-stack Express + Vite local server on port 3000
├── requirements.txt                # Root Python requirements pointer
├── package.json                    # Node/React scripts and dependencies
└── .env.example                    # Documented environment variable template (no secrets)
```

---

## Technology Stack & Purpose

| Layer | Technology | Role in CrimeVision AI |
| :--- | :--- | :--- |
| **Python AI/ML Backend** | Python 3.10+, Flask, PyTorch, HuggingFace `transformers` | Hosts official `RT-DETR` (`PekingU/rtdetr_r50vd`), `CLIP` (`openai/clip-vit-base-patch32`), `BLIP`, and `Whisper` (`openai/whisper-base`) pipelines (`backend/`). |
| **Media Processing** | OpenCV (`opencv-python-headless`) & `FFmpeg` | Performs 1Hz surveillance frame sampling (capped at 30s) and audio duration probing. |
| **Reasoning & Reports** | Groq (`llama-3.3-70b-versatile`) / `@google/genai`, `ReportLab` / `PDFKit` | Synthesizes grounded non-accusatory investigative scenarios, multilingual translations, and `%PDF-1.4` forensic reports, with deterministic offline fallbacks. |
| **Frontend & 3D Engine** | React 19, TypeScript, Tailwind CSS 4, `Three.js` | Renders the multi-tab forensic interface, 2D SVG bounding-box overlays, and interactive WebGL 3D room reconstruction. |
| **Persistence & Testing** | JSON `SessionStore`, Python `unittest` | Stores `session_<uuid>.json` case records on disk without requiring an external database server; validates logic via `test_validation.py`. |

---

## Local Setup & Execution Guide

### Prerequisites
- **Node.js 20+** and `npm`
- **Python 3.10+**
- **FFmpeg** (recommended for 1Hz surveillance video frame extraction; `sudo apt install ffmpeg`, `brew install ffmpeg`, or `winget install Gyan.FFmpeg`)

### Step 1: Clone & Configure Environment Variables

```bash
git clone <your-repo-url>
cd crime-vision-ai
cp .env.example .env
```

*(On Windows PowerShell: `Copy-Item .env.example .env`)*

Environment keys in `.env`:
- `GEMINI_API_KEY`: Required for live multimodal Image Forensics in Node/Express mode (and used by Python `VisionService` when local PyTorch checkpoints are not installed). Image Forensics never falls back to predefined or hardcoded detections.
- `GROQ_API_KEY`: Optional; enables Groq Llama-3.3 reasoning in Python Flask mode alongside local `RT-DETR`, `CLIP`, `BLIP`, and `Whisper` checkpoints.

### Step 2: Run the Application (Quickstart — Port 3000)

```bash
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser.

### Step 3: (Optional) Run the Full Python Flask + PyTorch Backend (Port 5000)

To execute local HuggingFace neural checkpoints (`RT-DETR`, `CLIP`, `BLIP`, `Whisper`) via Flask and proxy `/api/*` requests from port 3000 to port 5000:

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python3 backend/app.py
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\app.py
```

Then set `FLASK_BACKEND_URL="http://localhost:5000"` in `.env` and run `npm run dev` in a second terminal.

---

## Sample Media, Automated Testing & Evaluation

### Regenerate Synthetic Sample Assets
All sample images, witness WAV recordings, 10s/8s H.264 CCTV MP4 videos, and the ground-truth CSV dataset in `data/samples/` can be regenerated anytime:

```bash
python3 scripts/generate_samples.py
```

### Run Automated Unit & Validation Tests
Executes 9 unit and integration tests covering cross-modal consistency/conflict scoring, certainty markers, 1Hz hash-indexed timelines, Regex timestamp Q&A, SHA-256 validation, session persistence, vision/audio/PDF pipelines, and `/api/health`:

```bash
python3 -m unittest backend/tests/test_validation.py -v
```

### Run Quantitative Benchmark Evaluation
Evaluates the implemented algorithms on `data/samples/tabular/synthetic_forensic_benchmark.csv` and sample media, writing measured metrics to `outputs/evaluation/EVALUATION_SUMMARY.md`:

```bash
python3 scripts/run_evaluation.py
```

---

## Troubleshooting

- **`Unsupported <modality> format` error on upload**: Ensure images are `.jpg/.jpeg/.png/.webp/.bmp`, audio files are `.wav/.mp3/.m4a/.ogg/.flac`, and videos are `.mp4/.webm/.mov/.avi/.mkv` under 50 MB.
- **First-run HuggingFace download time**: When running `python backend/app.py` with `CRIMEVISION_LIGHTWEIGHT_MODE=false`, HuggingFace caches `RT-DETR`, `CLIP`, `BLIP`, and `Whisper` weights (~1.8 GB total) on first use. Set `CRIMEVISION_LIGHTWEIGHT_MODE=true` on low-RAM laptops for instant lightweight execution.
- **Protobuf / TensorFlow warnings**: `backend/app.py` automatically sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` and `USE_TF=0` before importing `transformers`.

---

## Responsible & Ethical Forensic AI Statement

CrimeVision AI is strictly an **investigative decision-support and academic research tool**:
- It **never** performs facial recognition, biometric identification, or demographic profiling.
- It **never** labels a human being as a criminal; detected figures are cataloged objectively as `"Human"` with spatial posture descriptors.
- All scenario hypotheses, classifications, and certainty markers represent algorithmic observations requiring independent verification by qualified human investigators.
