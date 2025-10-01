# VetRec Demo — Audio/Transcript → LLM → SOAP → Review/Diff → Save

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18%2B-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-%20%F0%9F%9A%80-009688.svg)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/React%20%2B%20Vite-Ready-61dafb.svg)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey.svg)](https://sqlite.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-available-success.svg)](https://ffmpeg.org/)
[![Gemini 2.x JSON Mode](https://img.shields.io/badge/Gemini-2.x-%23a855f7.svg)](https://ai.google.dev/)
[![faster-whisper](https://img.shields.io/badge/STT-faster--whisper-orange.svg)](https://github.com/guillaumekln/faster-whisper)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](#license)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> Turn short clinic **audio or text** into a **structured SOAP note** via Gemini 2.x (JSON mode). Clinicians can **review & edit**, see an **inline Diff**, and **save** to a mock PMS with an **audit trail**. Local STT works out-of-the-box (no cloud required); Google Cloud Speech is an optional toggle.
---
A pragmatic demo that turns **audio or text transcripts** into a structured **SOAP note** using Gemini 2.x, lets a clinician **review & edit**, shows a **Diff**, and **saves** to a mock PMS (SQLite) with an **audit trail**.

**Stack**
- Backend: FastAPI, Pydantic, SQLite, optional local STT (faster-whisper) or Google Cloud Speech.
- Frontend: React + Vite (TypeScript).
- LLM: Google Gemini 2.x (JSON mode) — with retry/fallback; or stubbed output for offline demos.

---

## Project Structure
```
vetrec-demo/
├── backend/
│ ├── app/
│ │ ├── init.py
│ │ ├── main.py # FastAPI routes: /ingest, /generate, /pms/save, /audit, /health
│ │ ├── models.py # Pydantic schemas (SOAPNote, requests)
│ │ ├── db.py # SQLite helpers
│ │ ├── llm.py # Gemini 2.x JSON-mode call w/ retry + stub fallback
│ │ ├── prompts.py # System/user prompts for SOAP
│ │ ├── stt_local.py # Local STT (faster-whisper)
│ │ ├── stt_google.py # (optional) Google Cloud Speech v2 STT
│ │ └── stt_router.py # Selects STT provider via env: local | google
│ ├── .env.example
│ └── demo.sqlite3 # created at runtime
├── frontend/
│ └── src/
│ ├── api.ts # fetch helpers
│ ├── types.ts # SOAP types
│ ├── App.tsx # UI (Editor / Diff / Audit)
│ ├── components/
│ │ └── DiffPanel.tsx
│ ├── utils/
│ │ └── diff.ts
│ ├── styles.css
│ ├── main.tsx
│ └── index.html
├── sample_data/
│ └── sample_transcript.txt
└── README.md
```
---

## Prerequisites

- **Node.js 18+**
- **Python 3.10+**
- **FFmpeg** on PATH (you have it: `ffmpeg -version`)
- (Optional) **Google AI Studio** key for Gemini
- (Optional) **Google Cloud** creds for Speech-to-Text v2

---

## 1) Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate

# Core deps
pip install --upgrade pip
pip install fastapi uvicorn "pydantic[dotenv]" python-multipart httpx sqlalchemy aiosqlite

# LLM + env
pip install google-generativeai python-dotenv

# Local STT (default path, uses your FFmpeg)
pip install faster-whisper


Create .env (copy from example and edit):

cp .env.example .env


.env example

# ---- LLM ----
GEMINI_API_KEY=YOUR_AI_STUDIO_KEY   # leave blank to use stub
MODEL_NAME=gemini-2.0-flash         # or gemini-2.5-flash if available

# ---- STT provider (audio→text) ----
STT_PROVIDER=local                  # local | google
WHISPER_MODEL=tiny.en               # tiny.en | base.en | small.en

# ---- Google Cloud Speech (optional) ----
GOOGLE_APPLICATION_CREDENTIALS=/abs/path/service-account.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=global
GCP_SPEECH_RECOGNIZER=projects/your-project-id/locations/global/recognizers/_
STT_MAX_SECONDS=120


Run backend:

uvicorn app.main:app --reload --port 8000


Health check:

GET http://localhost:8000/health
# -> {"provider":"gemini" | "stub","model":"gemini-2.0-flash"}

```
---

2) Frontend Setup

```bash
cd ../frontend
npm install
npm run dev


Open the Vite URL (usually http://localhost:5173).

```

3) How to Use (Happy Path)

**Ingest**

- Upload audio or paste a transcript.

- Click Ingest (saves file + transcript; runs STT if audio-only).

**Generate**

- Click Generate SOAP (Gemini 2.x JSON mode → Pydantic-validation).

- If no API key/issue: graceful stub note to keep demo moving.

**Review & Edit**

- Tweak Subjective / Objective / Assessment / Plan.

**Diff**

- Open Diff tab to see changes vs generated (or vs transcript).

**Save & Audit**

- Click Save to Mock PMS → view Audit entries.

---

4) Audio Testing

macOS quick sample:

```bash
say -v Samantha -r 170 -o sample.aiff "Bella, three year old lab, coughing for two days, eating well. Vitals stable."
ffmpeg -y -i sample.aiff -ar 16000 -ac 1 sample.wav
```


Upload sample.wav, leave transcript empty, Ingest → Generate.

---

5) Switch Providers
**LLM**

- Uses Gemini 2.x with response_mime_type="application/json".

- Set GEMINI_API_KEY + MODEL_NAME in .env.

- Leave GEMINI_API_KEY blank to force stub output (offline demo).

**STT (audio→text)**

- Local (default): STT_PROVIDER=local (no cloud, uses faster-whisper).

- Google Cloud: STT_PROVIDER=google and set the GCP env vars.

---

6) API Endpoints (dev)

POST /ingest — form-data: file(audio, optional), transcript(text, optional)

- Saves ingest; if audio-only, runs STT.

- Response: { "ingest_id": "..." }

POST /generate — body: { "ingest_id": "..." }

- Calls LLM → SOAP JSON; validates; audits.

POST /pms/save — body: { "patient_id": "...", "note": { ...SOAP... } }

- Saves to SQLite mock PMS; audits.

GET /audit — recent events

GET /health — provider/model status

GET /version — (optional) library/model echo if you added it

---

7) Troubleshooting

- Blank Diff: edit a field first (or switch compare to “Transcript vs Current”).

- Gemini returns empty: check .env key; try MODEL_NAME=gemini-2.0-flash; the backend retries then falls back to stub.

- 429/5xx: retry/backoff is built-in; keep transcripts short.

- STT slow: use WHISPER_MODEL=tiny.en and short files (≤2–3 min).

- FFmpeg not found: ensure ffmpeg -version works in the same terminal.

---

8) Production Considerations (next steps)

- DB: Postgres + migrations; idempotent writes; queues for STT/LLM.

- Security: SSO/RBAC, audit read/write trails, PHI redaction, KMS at-rest.

- PMS: implement real adapters (ezyVet/IDEXX) behind an interface seam.

- Metrics: latency p95, error rate, adoption, edit distance vs generated.

---

## License / Data

Demo only. No real PHI. Replace any uploaded content with synthetic data for tests.
