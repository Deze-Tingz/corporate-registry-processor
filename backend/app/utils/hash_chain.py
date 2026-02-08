import hashlib
import json
from datetime import datetime
from uuid import UUID


def _json_serial(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def compute_entry_hash(
    previous_hash: str,
    timestamp: datetime,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    details: dict,
) -> str:
    payload = json.dumps(
        {
            "previous_hash": previous_hash,
            "timestamp": timestamp.isoformat(),
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": details,
        },
        sort_keys=True,
        default=_json_serial,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


GENESIS_HASH = "0" * 64
