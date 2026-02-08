import uuid
from datetime import datetime

from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    document_id: uuid.UUID


class ClassificationOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_type: str
    confidence_score: float
    reasoning: str
    extracted_fields: dict
    limitations: str | None
    model_version: str
    prompt_version: str
    ai_available: bool
    processing_time_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
