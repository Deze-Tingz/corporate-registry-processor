from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.classification import Classification
from app.schemas.classification import ClassificationOut, ClassifyRequest
from app.services.classifier_service import classify_document

router = APIRouter(prefix="/api/classifications", tags=["classifications"])


@router.post("", response_model=ClassificationOut, status_code=status.HTTP_201_CREATED)
async def trigger_classification(
    body: ClassifyRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        classification = await classify_document(db, body.document_id, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return classification


@router.get("/{document_id}", response_model=ClassificationOut)
async def get_classification(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Classification).where(Classification.document_id == document_id)
    )
    classification = result.scalar_one_or_none()
    if classification is None:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification
