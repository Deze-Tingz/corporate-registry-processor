import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.utils.hash_chain import GENESIS_HASH, compute_entry_hash


async def _get_previous_hash(db: AsyncSession) -> str:
    result = await db.execute(
        select(AuditLog.entry_hash).order_by(AuditLog.id.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    return row if row else GENESIS_HASH


async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    details = details or {}
    now = datetime.now(timezone.utc)
    previous_hash = await _get_previous_hash(db)

    entry_hash = compute_entry_hash(
        previous_hash=previous_hash,
        timestamp=now,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )

    entry = AuditLog(
        timestamp=now,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    await db.flush()
    return entry


async def verify_chain(db: AsyncSession) -> dict:
    result = await db.execute(select(AuditLog).order_by(AuditLog.id.asc()))
    entries = result.scalars().all()

    if not entries:
        return {"valid": True, "checked": 0, "broken_at": None}

    expected_prev = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != expected_prev:
            return {"valid": False, "checked": entry.id, "broken_at": entry.id}

        recomputed = compute_entry_hash(
            previous_hash=entry.previous_hash,
            timestamp=entry.timestamp,
            user_id=entry.user_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            details=entry.details,
        )
        if recomputed != entry.entry_hash:
            return {"valid": False, "checked": entry.id, "broken_at": entry.id}

        expected_prev = entry.entry_hash

    return {"valid": True, "checked": len(entries), "broken_at": None}
