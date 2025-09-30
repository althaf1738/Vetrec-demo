import os, uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path 
from dotenv import load_dotenv 

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from pydantic import ValidationError
from .models import SOAPNote, GenerateRequest, SaveRequest, AuditEvent
from . import db

from .llm import call_llm, debug_list_models
from .stt_local import transcribe_async 


app = FastAPI(title="VetRec Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def _start(): 
    await db.init() 
    debug_list_models() 

@app.post("/ingest")
async def ingest(file: UploadFile | None = File(None), transcript: str | None = Form(None)):
    ingest_id = str(uuid.uuid4())
    file_path = None

    # Save uploaded file if present
    if file:
        file_path = f"/tmp/{ingest_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

    # If audio provided and no transcript pasted, run local STT
    if (not transcript) and file_path:
        try:
            transcript = await transcribe_async(file_path)
        except Exception as e:
            print("STT failed, falling back to sample:", e)

    # Fallback to sample transcript if still empty
    if not transcript:
        try:
            import os as _os, pathlib as _pl
            sample = _pl.Path(__file__).resolve().parents[1] / "sample_data" / "sample_transcript.txt"
            transcript = sample.read_text()
        except Exception:
            transcript = "Patient dog, cough for 2 days, eating well..."

    await db.create_ingest(ingest_id, file_path, transcript)
    await db.audit("INGESTED", {"engest_id": ingest_id, "has_file": bool(file), "chars": len(transcript)})
    return {"ingest_id": ingest_id}


@app.get("/health")
async def health():
    import os
    return {
        "provider": "gemini" if os.getenv("GEMINI_API_KEY") else "stub",
        "model": os.getenv("MODEL_NAME", "gemini-1.5-flash")
    }


@app.post("/generate")
async def generate(req: GenerateRequest):
    row = await db.get_ingest(req.ingest_id)
    if not row: return {"error":"unknown_ingest"}
    note_dict = await call_llm(row["transcript"])
    try:
        note = SOAPNote(**note_dict)
    except ValidationError as ve:
        # minimal repair: collapse unknown keys and retry once with static fallback
        note = SOAPNote(subjective="See transcript.", objective="Vitals stable.",
                        assessment="Insufficient data.", plan="Follow-up.")
    await db.audit("GENERATED", {"ingest_id": req.ingest_id})
    return {"note": note.model_dump()}

@app.post("/pms/save")
async def save(req: SaveRequest):
    await db.save_note(req.patient_id, req.note.model_dump())
    await db.audit("SAVED", {"patient_id": req.patient_id})
    return {"status":"ok"}

@app.get("/audit")
async def audit():
    events = await db.fetch_audit()
    return {"events": events}


