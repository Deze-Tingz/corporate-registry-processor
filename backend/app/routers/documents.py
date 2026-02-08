import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import CurrentUser, RequireRole, get_current_user
from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentList, DocumentOut, DocumentTextOut
from app.services import audit_service, storage_service
from app.services.ocr_service import extract_text

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum size")

    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    if mime not in settings.allowed_mime_types:
        raise HTTPException(status_code=415, detail=f"File type {mime} not allowed")

    tracking_id = storage_service.generate_tracking_id()
    suffix = Path(file.filename).suffix
    file_hash = storage_service.compute_hash_from_bytes(content)
    saved_path = storage_service.save_uploaded_file(content, tracking_id, suffix)

    # Extract text
    extracted = extract_text(saved_path, mime)

    doc = Document(
        tracking_id=tracking_id,
        original_filename=file.filename,
        original_path=str(saved_path),
        file_hash_sha256=file_hash,
        file_size_bytes=len(content),
        mime_type=mime,
        extracted_text=extracted or None,
        status="pending_classification",
        intake_method="upload",
        submitted_by=user.id,
    )
    db.add(doc)
    await db.flush()

    await audit_service.log_action(
        db,
        action="document_upload",
        resource_type="document",
        resource_id=doc.id,
        user_id=user.id,
        details={"filename": file.filename, "tracking_id": tracking_id, "size": len(content)},
    )
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).order_by(Document.created_at.desc())
    count_query = select(func.count(Document.id))

    if status_filter:
        query = query.where(Document.status == status_filter)
        count_query = count_query.where(Document.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()

    return DocumentList(items=items, total=total)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.original_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type,
        filename=doc.original_filename,
    )


@router.get("/{document_id}/text", response_model=DocumentTextOut)
async def get_document_text(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentTextOut(id=doc.id, tracking_id=doc.tracking_id, extracted_text=doc.extracted_text)
