import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    details: dict
    ip_address: str | None
    user_agent: str | None
    previous_hash: str
    entry_hash: str

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    items: list[AuditLogOut]
    total: int


class AuditChainVerification(BaseModel):
    valid: bool
    checked: int
    broken_at: int | None
