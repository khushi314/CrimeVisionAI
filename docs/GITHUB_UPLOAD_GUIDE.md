# Preparing & Uploading CrimeVision AI to GitHub

Follow these exact steps on your local machine to verify repository cleanliness, initialize Git, and push your capstone project to GitHub without committing secrets, virtual environments, or oversized binary weights.

---

## 1. Pre-Upload Cleanliness Checklist

Verify `.gitignore` excludes:
- `.env` and `.env.*` (except `.env.example`)
- `venv/`, `.venv/` (Python virtual environments)
- `node_modules/` and `dist/`
- `models/checkpoints/` (`*.pth`, `*.pt`, `*.safetensors`, `*.onnx` neural weights — downloaded automatically by HuggingFace on first run)
- Runtime uploads (`data/uploads/*`, `data/temp_frames/*`, `data/sessions/*.json`, `outputs/reports/*.pdf`)

Run a quick check before staging:

```bash
# Confirm no .env file or API keys exist in tracked files
ls -la .env 2>/dev/null && echo "Note: .env exists locally and is ignored by .gitignore"

# Confirm synthetic sample files are lightweight (< 2 MB total)
du -sh data/samples/*
```

---

## 2. Step-by-Step Git & GitHub Commands

```bash
# 1. Initialize Git repository (if not already initialized)
git init
git branch -M main

# 2. Verify what Git will stage (ensure node_modules/, venv/, and .env do NOT appear)
git status

# 3. Stage project source code, sample media, tests, and academic documentation
git add .

# 4. Double-check staged files and sizes
git status

# 5. Create clean initial academic submission commit
git commit -m "feat: complete CrimeVision AI multimodal forensic analysis platform and documentation"

# 6. Create an empty repository on GitHub (e.g., https://github.com/<your-username>/crime-vision-ai)
#    Do NOT initialize with a conflicting README on GitHub. Then link remote and push:
git remote add origin https://github.com/<your-username>/crime-vision-ai.git
git push -u origin main
```

---

## 3. Clean-Clone Grading Verification (Recommended Before Submission)

To verify your evaluator or professor can clone and run your submission from scratch:

```bash
git clone https://github.com/<your-username>/crime-vision-ai.git crime-vision-verify
cd crime-vision-verify

# Copy environment template
cp .env.example .env

# Run automated Python unit tests
python3 -m unittest backend/tests/test_validation.py -v

# Install frontend/gateway packages and launch local application
npm install
npm run dev
```
