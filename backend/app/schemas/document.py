import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    tracking_id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: str
    intake_method: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentOut):
    original_path: str
    processed_path: str | None
    file_hash_sha256: str
    extracted_text: str | None
    submitted_by: uuid.UUID | None


class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int


class DocumentTextOut(BaseModel):
    id: uuid.UUID
    tracking_id: str
    extracted_text: str | None
