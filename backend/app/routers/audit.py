import csv
import io
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, RequireRole
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditChainVerification, AuditLogList, AuditLogOut
from app.services.audit_service import verify_chain

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditLogList)
async def query_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = None,
    resource_type: str | None = None,
    user: CurrentUser = Depends(RequireRole("supervisor")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.id.desc())
    count_query = select(func.count(AuditLog.id))

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()
    return AuditLogList(items=items, total=total)


@router.get("/verify", response_model=AuditChainVerification)
async def verify_audit_chain(
    user: CurrentUser = Depends(RequireRole("supervisor")),
    db: AsyncSession = Depends(get_db),
):
    result = await verify_chain(db)
    return AuditChainVerification(**result)


@router.get("/export/csv")
async def export_csv(
    action: str | None = None,
    resource_type: str | None = None,
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.id.asc())
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    result = await db.execute(query)
    entries = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "timestamp", "user_id", "action", "resource_type",
        "resource_id", "details", "ip_address", "previous_hash", "entry_hash",
    ])
    for e in entries:
        writer.writerow([
            e.id, e.timestamp.isoformat(), str(e.user_id) if e.user_id else "",
            e.action, e.resource_type, str(e.resource_id) if e.resource_id else "",
            json.dumps(e.details), e.ip_address or "",
            e.previous_hash, e.entry_hash,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )


@router.get("/export/json")
async def export_json(
    action: str | None = None,
    resource_type: str | None = None,
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.id.asc())
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    result = await db.execute(query)
    entries = result.scalars().all()

    data = [AuditLogOut.model_validate(e).model_dump(mode="json") for e in entries]
    return data
