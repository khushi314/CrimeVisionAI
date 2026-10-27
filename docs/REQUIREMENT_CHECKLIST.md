# Official Workflow Requirement Checklist & Traceability Matrix

Primary Source of Truth: **CrimeVision AI — Intelligent Multimodal Forensic Analysis Platform** (61-page SkillWallet Capstone Workflow PDF).

> **Missing External Resource Disclosure**: Only the 61-page official workflow specification PDF was uploaded. No separate university `.docx` or `.md` report template or external real-world crime dataset archive was attached. Accordingly:
> 1. `PROJECT_REPORT.md` follows standard 16-section computer science capstone report structure.
> 2. `scripts/generate_samples.py` deterministically synthesizes legally redistributable, privacy-safe staged forensic photographs, witness audio recordings, 1Hz-compatible surveillance CCTV clips, and a ground-truth CSV benchmark dataset under `data/samples/`.

---

## 1. Mandatory Features (Specified in Milestones 1–6)

| Milestone & Activity | Official Requirement | Implementation File(s) | Output / Verification Artifact | Status |
| :--- | :--- | :--- | :--- | :---: |
| **M1 — Act 1.1 & 1.2** | Isolated Python `venv`, `requirements.txt`, runtime guards (`PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`, `USE_TF=0`, `TF_CPP_MIN_LOG_LEVEL=2`), GPU/CPU resolution | `requirements.txt`, `backend/requirements.txt`, `backend/app.py`, `backend/utils/model_loader.py` | Verified via `python3 -m unittest` | Implemented |
| **M2 — Act 2.1** | RT-DETR object/person/weapon detection (`Humans`, `weapons`, `objects` counts + bounding boxes) & zero-shot CLIP indoor/outdoor scene location classification | `backend/services/vision_service.py`, `server/geminiForensicEngine.ts` | `/api/analyze-image`, `ImageAnalysisView.tsx` | Implemented |
| **M2 — Act 2.2** | BLIP visual captioning, structured 2-line `AI Scene Summary` (`Summary Type` + `Brief Description`), `Actions Detected`, `Evidence Facts`, **3 Investigative Scenarios**, and **Three.js 3D Scene Reconstruction** | `backend/services/vision_service.py`, `src/components/Scene3DReconstruction.tsx`, `src/components/ImageAnalysisView.tsx` | Interactive 3D WebGL room + 3 scenario cards | Implemented |
| **M3 — Act 3.1** | Witness audio upload (`.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`), Whisper (`openai/whisper-base`) speech-to-text with segment timestamps, and 120s timeout protection | `backend/services/audio_service.py`, `backend/audio_module/transcription.py`, `backend/audio_module/api.py` | `/api/analyze-audio`, `AudioAnalysisView.tsx` | Implemented |
| **M3 — Act 3.2** | `AI Intelligence Report` (`AI Summary`, `Event Type`, `Location`), **Multilingual Translations (English, Hindi, Telugu, French)**, and `MM:SS` Crime Event Timeline | `backend/audio_module/crime_analysis.py`, `src/components/AudioAnalysisView.tsx` | 4-language interactive tabs + clickable audio timeline | Implemented |
| **M4 — Act 4.1** | Surveillance CCTV upload (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`), OpenCV/FFmpeg **1Hz (`1 frame/sec`) sampling** capped at 30s, per-frame RT-DETR detection & aggregation | `backend/video_module/processor.py`, `backend/video_module/detector.py`, `backend/video_module/api.py` | `/api/analyze-video`, `data/temp_frames/` | Implemented |
| **M4 — Act 4.2** | Frame captioning, `AI Visual Summary`, Sequence Crime Classification (`NORMAL ACTIVITY` / alert + `Reason`), and **Hash-Indexed (`O(1)`) Second-by-Second Event Timeline** (`00:00`, `00:01`...) | `backend/video_module/captions.py`, `backend/video_module/classifier.py`, `backend/video_module/timeline.py`, `src/components/VideoAnalysisView.tsx` | Click-to-seek video timeline + classification banner | Implemented |
| **M5 — Act 5.1** | Cross-modal consistency & conflict audit (`FusionService._check_consistency`) corroborating spatial locations & objects across vision and audio (`overall_score`, `matches`, `conflicts`) | `backend/services/fusion_service.py`, `server/geminiForensicEngine.ts`, `src/components/MultimodalFusionView.tsx` | `/api/fuse`, `/api/process/complete/<case_id>` | Implemented |
| **M5 — Act 5.2** | Forensic certainty markers (`high >= 0.8`, `medium >= 0.6`, `low < 0.6`), `temporal_uncertainty` (`known` vs `unknown`), `SessionStore` JSON persistence (`session_<uuid>.json`), and **Regex Timestamp Lookup + Grounded RAG Chat** (`temperature=0.1`, `"Information not found"` rule) | `backend/services/session_store.py`, `backend/services/chat_service.py`, `src/components/ForensicChatPanel.tsx` | `data/sessions/session_<uuid>.json`, `/api/chat/<mode>` | Implemented |
| **M6 — Act 6.1** | Unified multi-tab Forensic Dashboard connecting Image, Audio, Video, Multimodal Fusion, and Grounded Chat | `src/App.tsx`, `src/components/*.tsx`, `server.ts` | Local web UI on `http://localhost:3000` | Implemented |
| **M6 — Act 6.2** | Automated validation unit test suite (`test_fusion_logic_consistency`, `test_api_health`, timeline, chat, PDF) & **Downloadable PDF Forensic Report** | `backend/tests/test_validation.py`, `backend/services/report_service.py`, `backend/routes/results_routes.py` | `outputs/reports/report_<id>.pdf`, `/api/report/<session_id>` | Implemented |

---

## 2. Optional Practical Improvements Included

1. **SHA-256 Chain-of-Custody Hashing**: Every uploaded or sample evidence file has its SHA-256 cryptographic digest computed (`backend/utils/file_handler.py` & `server/sessionStore.ts`) and printed inside the downloadable PDF Forensic Report.
2. **Optional SAM Mask Loader**: `backend/utils/model_loader.py` supports loading Segment Anything (`vit_b`) when `SAM_CHECKPOINT_PATH` is configured, without blocking execution on standard student laptops lacking 4GB+ extra VRAM.
3. **Deterministic Synthetic Sample Suite & Reproducible Benchmark Runner**: `scripts/generate_samples.py` and `scripts/run_evaluation.py` generate privacy-safe test media and verifiable CSV accuracy metrics (`outputs/evaluation/benchmark_results.json`).
4. **Dual-Runtime Compatibility**: Supports running the standalone Python Flask + PyTorch server (`backend/app.py` on port 5000) proxied through Vite/Express OR running lightweight/Gemini-backed local preview (`npm run dev` on port 3000).

---

## 3. Features Explicitly Excluded (Out of Scope / Ethical Boundaries)

- **Cloud Hosting / Production Deployment**: Excluded per explicit user instructions (local execution and GitHub repository preparation only).
- **Biometric Facial Recognition / Suspect Identity Matching**: Excluded — not requested in the workflow PDF and poses severe privacy and wrongful-accusation risks.
- **Demographic / Appearance-Based Criminality Prediction**: Strictly prohibited — individuals are cataloged solely as `"Human"` with objective posture descriptions.
- **Live RTSP IP-Camera Streaming**: Not specified in the workflow PDF; video analysis operates on uploaded `.mp4`/`.avi`/`.mov`/`.webm` clips up to 30 seconds at 1Hz.
