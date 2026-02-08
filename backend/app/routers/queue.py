from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, RequireRole
from app.models.queue import ProcessingQueueItem
from app.schemas.queue import QueueItemList, QueueItemOut, QueueStatusUpdate
from app.services import audit_service

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("", response_model=QueueItemList)
async def list_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    queue_name: str | None = None,
    user: CurrentUser = Depends(RequireRole("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    query = select(ProcessingQueueItem).order_by(
        ProcessingQueueItem.priority.desc(),
        ProcessingQueueItem.created_at.asc(),
    )
    count_query = select(func.count(ProcessingQueueItem.id))

    if status_filter:
        query = query.where(ProcessingQueueItem.status == status_filter)
        count_query = count_query.where(ProcessingQueueItem.status == status_filter)
    if queue_name:
        query = query.where(ProcessingQueueItem.queue_name == queue_name)
        count_query = count_query.where(ProcessingQueueItem.queue_name == queue_name)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()
    return QueueItemList(items=items, total=total)


@router.patch("/{item_id}", response_model=QueueItemOut)
async def update_queue_status(
    item_id: str,
    body: QueueStatusUpdate,
    user: CurrentUser = Depends(RequireRole("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcessingQueueItem).where(ProcessingQueueItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")

    if body.status not in ("pending", "processing", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status")

    item.status = body.status
    if body.status == "processing":
        item.assigned_to = user.id
    elif body.status == "completed":
        item.completed_at = datetime.now(timezone.utc)

    await db.flush()
    await audit_service.log_action(
        db,
        action=f"queue_{body.status}",
        resource_type="queue_item",
        resource_id=item.id,
        user_id=user.id,
    )
    await db.commit()
    await db.refresh(item)
    return item
