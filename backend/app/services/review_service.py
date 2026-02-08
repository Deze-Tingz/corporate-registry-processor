import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import Classification
from app.models.document import Document
from app.models.review import Review
from app.services import audit_service


async def get_review_queue(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    escalated_only: bool = False,
) -> tuple[list[dict], int]:
    """Get documents that are classified and awaiting review."""
    base = (
        select(
            Document.id.label("document_id"),
            Document.tracking_id,
            Document.original_filename,
            Document.status,
            Document.created_at,
            Classification.document_type,
            Classification.confidence_score,
            Classification.ai_available,
        )
        .join(Classification, Classification.document_id == Document.id)
        .where(Document.status.in_(["classified", "escalated"]))
    )

    if escalated_only:
        base = base.where(Document.status == "escalated")

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = base.order_by(Document.created_at.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "document_id": r.document_id,
            "tracking_id": r.tracking_id,
            "original_filename": r.original_filename,
            "document_type": r.document_type,
            "confidence_score": float(r.confidence_score),
            "ai_available": r.ai_available,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return items, total


async def submit_review(
    db: AsyncSession,
    reviewer_id: uuid.UUID,
    document_id: uuid.UUID,
    classification_id: uuid.UUID,
    decision: str,
    corrected_document_type: str | None = None,
    corrected_fields: dict | None = None,
    correction_reason: str | None = None,
    escalation_reason: str | None = None,
    escalated_to: uuid.UUID | None = None,
) -> Review:
    if decision not in ("approved", "corrected", "escalated"):
        raise ValueError(f"Invalid decision: {decision}")

    # Verify document exists
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise ValueError("Document not found")

    review = Review(
        document_id=document_id,
        classification_id=classification_id,
        reviewer_id=reviewer_id,
        decision=decision,
        corrected_document_type=corrected_document_type,
        corrected_fields=corrected_fields,
        correction_reason=correction_reason,
        escalation_reason=escalation_reason,
        escalated_to=escalated_to,
    )
    db.add(review)

    # Update document status based on decision
    if decision == "approved":
        doc.status = "approved"
    elif decision == "corrected":
        doc.status = "corrected"
    elif decision == "escalated":
        doc.status = "escalated"

    await db.flush()

    await audit_service.log_action(
        db,
        action=f"review_{decision}",
        resource_type="document",
        resource_id=document_id,
        user_id=reviewer_id,
        details={
            "decision": decision,
            "classification_id": str(classification_id),
            "corrected_type": corrected_document_type,
            "escalation_reason": escalation_reason,
        },
    )
    await db.commit()
    await db.refresh(review)
    return review


async def supervisor_override(
    db: AsyncSession,
    supervisor_id: uuid.UUID,
    document_id: uuid.UUID,
    classification_id: uuid.UUID,
    corrected_document_type: str | None = None,
    corrected_fields: dict | None = None,
    override_reason: str = "",
) -> Review:
    """Supervisor overrides a previous escalation or review."""
    review = Review(
        document_id=document_id,
        classification_id=classification_id,
        reviewer_id=supervisor_id,
        decision="corrected",
        corrected_document_type=corrected_document_type,
        corrected_fields=corrected_fields,
        correction_reason=f"[SUPERVISOR OVERRIDE] {override_reason}",
    )
    db.add(review)

    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if doc:
        doc.status = "corrected"

    await db.flush()

    await audit_service.log_action(
        db,
        action="supervisor_override",
        resource_type="document",
        resource_id=document_id,
        user_id=supervisor_id,
        details={
            "override_reason": override_reason,
            "corrected_type": corrected_document_type,
        },
    )
    await db.commit()
    await db.refresh(review)
    return review
