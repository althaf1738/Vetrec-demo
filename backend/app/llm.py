import os, json, time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from .prompts import SOAP_SYSTEM, SOAP_USER

# --- local deterministic fallback so demo never blocks ---
def _stub_note() -> dict:
    return {
        "subjective": "Dog presented for cough, owner reports onset 2 days ago.",
        "objective": "T 102.5F, mild wheeze, active, eating.",
        "assessment": "Likely mild tracheobronchitis.",
        "plan": "Doxycycline 5mg/kg BID x7d, rest, recheck 1 week."
    }

def _extract_text(resp) -> str | None:
    """
    Gemini 2.x sometimes returns no quick .text; pull from candidates/parts when needed.
    Also handle cases where no parts are emitted (safety/finish_reason).
    """
    t = getattr(resp, "text", None)
    if t:
        return t
    cand = getattr(resp, "candidates", None)
    if cand:
        c0 = cand[0]
        content = getattr(c0, "content", None)
        if content and getattr(content, "parts", None):
            return "".join(getattr(p, "text", "") for p in content.parts if getattr(p, "text", None))
    return None

def _blocked_or_empty(resp) -> bool:
    cand = getattr(resp, "candidates", None)
    if not cand:
        return True
    c0 = cand[0]
    # finish_reason 2 often means SAFETY or NO_CONTENT
    fr = getattr(c0, "finish_reason", None)
    txt = _extract_text(resp)
    return (txt is None) or (fr is not None and int(fr) != 1)  # 1 is STOP in many SDKs

def _safety_settings_relaxed():
    # Start relaxed to avoid non-medical blocks; tighten later if needed.
    return {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT:       HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:      HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUAL_CONTENT:   HarmBlockThreshold.BLOCK_NONE,
    }

def _gen_config(max_tokens=600, temp=0.2):
    return GenerationConfig(
        response_mime_type="application/json",
        temperature=temp,
        max_output_tokens=max_tokens,
    )

def _compose_prompt(transcript: str) -> list:
    # 2.x supports system_instruction; user goes in content list
    user = SOAP_USER.format(transcript=transcript[:8000])
    return [user]

# --- Optional: list available models for your key (run once on startup to verify) ---
def debug_list_models():
    try:
        models = genai.list_models()
        print("=== Gemini models that support generateContent ===")
        for m in models:
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                print(" -", m.name)
        print("=== end ===")
    except Exception as e:
        print("Model listing failed:", e)

# --- Main entry used by your app ---
async def call_llm(transcript: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _stub_note()

    genai.configure(api_key=api_key)

    # Prefer 2.x family; you can set MODEL_NAME in .env to gemini-2.5-flash if your key has it
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    # Build model with system instruction (SOAP schema constraint lives in SOAP_SYSTEM)
    model = genai.GenerativeModel(model_name, system_instruction=SOAP_SYSTEM)

    # safety = _safety_settings_relaxed()
    cfg = _gen_config(max_tokens=700, temp=0.15)

    # First try
    try:
        resp = model.generate_content(
            _compose_prompt(transcript),
            generation_config=cfg,
        )
        txt = _extract_text(resp)
        if txt:
            return json.loads(txt)
        # If no text or blocked, fall through to retry with safer params
    except Exception as e:
        print(f"Gemini call error (first attempt): {e}")

    # Retry once: lower temperature, raise tokens slightly, short sleep
    time.sleep(0.6)
    cfg_retry = _gen_config(max_tokens=900, temp=0.0)
    try:
        resp = model.generate_content(
            _compose_prompt(transcript),
            generation_config=cfg_retry,
        )
        txt = _extract_text(resp)
        if txt:
            return json.loads(txt)
        # last resort
        print("Gemini returned no JSON content on retry; using stub.")
    except Exception as e:
        print(f"Gemini call error (retry): {e}")

    return _stub_note()
