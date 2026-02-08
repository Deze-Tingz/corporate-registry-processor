import uuid
from datetime import datetime

from pydantic import BaseModel


class ReviewSubmit(BaseModel):
    document_id: uuid.UUID
    classification_id: uuid.UUID
    decision: str  # approved | corrected | escalated
    corrected_document_type: str | None = None
    corrected_fields: dict | None = None
    correction_reason: str | None = None
    escalation_reason: str | None = None
    escalated_to: uuid.UUID | None = None


class ReviewOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    classification_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    corrected_document_type: str | None
    corrected_fields: dict | None
    correction_reason: str | None
    escalation_reason: str | None
    escalated_to: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueItem(BaseModel):
    document_id: uuid.UUID
    tracking_id: str
    original_filename: str
    document_type: str
    confidence_score: float
    ai_available: bool
    status: str
    created_at: datetime


class ReviewQueueList(BaseModel):
    items: list[ReviewQueueItem]
    total: int


class SupervisorOverride(BaseModel):
    document_id: uuid.UUID
    classification_id: uuid.UUID
    corrected_document_type: str | None = None
    corrected_fields: dict | None = None
    override_reason: str
