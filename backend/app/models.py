from pydantic import BaseModel, Field
from typing import Literal, Dict, Any

class SOAPNote(BaseModel):
    subjective: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    assessment: str = Field(min_length=1)
    plan: str = Field(min_length=1)

class GenerateRequest(BaseModel):
    ingest_id: str

class SaveRequest(BaseModel):
    patient_id: str
    note: SOAPNote

class AuditEvent(BaseModel):
    action: Literal["INGESTED","GENERATED","SAVED"]
    meta: Dict[str, Any]
    at_iso: str
