import uuid
from datetime import datetime

from pydantic import BaseModel


class QueueItemOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    review_id: uuid.UUID
    queue_name: str
    priority: int
    status: str
    assigned_to: uuid.UUID | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class QueueItemList(BaseModel):
    items: list[QueueItemOut]
    total: int


class QueueStatusUpdate(BaseModel):
    status: str  # pending | processing | completed
