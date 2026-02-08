from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, RequireRole, get_current_user
from app.schemas.review import (
    ReviewOut,
    ReviewQueueItem,
    ReviewQueueList,
    ReviewSubmit,
    SupervisorOverride,
)
from app.services.review_service import (
    get_review_queue,
    submit_review,
    supervisor_override,
)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/queue", response_model=ReviewQueueList)
async def review_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(RequireRole("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_review_queue(db, skip=skip, limit=limit)
    return ReviewQueueList(
        items=[ReviewQueueItem(**i) for i in items],
        total=total,
    )


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def submit(
    body: ReviewSubmit,
    user: CurrentUser = Depends(RequireRole("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    try:
        review = await submit_review(
            db,
            reviewer_id=user.id,
            document_id=body.document_id,
            classification_id=body.classification_id,
            decision=body.decision,
            corrected_document_type=body.corrected_document_type,
            corrected_fields=body.corrected_fields,
            correction_reason=body.correction_reason,
            escalation_reason=body.escalation_reason,
            escalated_to=body.escalated_to,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return review


@router.get("/escalated", response_model=ReviewQueueList)
async def escalated_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(RequireRole("supervisor")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_review_queue(db, skip=skip, limit=limit, escalated_only=True)
    return ReviewQueueList(
        items=[ReviewQueueItem(**i) for i in items],
        total=total,
    )


@router.post("/override", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def override(
    body: SupervisorOverride,
    user: CurrentUser = Depends(RequireRole("supervisor")),
    db: AsyncSession = Depends(get_db),
):
    try:
        review = await supervisor_override(
            db,
            supervisor_id=user.id,
            document_id=body.document_id,
            classification_id=body.classification_id,
            corrected_document_type=body.corrected_document_type,
            corrected_fields=body.corrected_fields,
            override_reason=body.override_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return review
