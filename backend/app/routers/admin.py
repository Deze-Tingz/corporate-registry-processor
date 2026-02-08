from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, RequireRole
from app.models.document import Document
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import audit_service
from app.services.auth_service import create_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    body: UserCreate,
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = await create_user(db, body.email, body.full_name, body.password, body.role)

    await audit_service.log_action(
        db,
        action="user_created",
        resource_type="user",
        resource_id=new_user.id,
        user_id=user.id,
        details={"email": body.email, "role": body.role},
    )
    await db.commit()
    return new_user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdate,
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.full_name is not None:
        target.full_name = body.full_name
    if body.role is not None:
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active

    await db.flush()
    await audit_service.log_action(
        db,
        action="user_updated",
        resource_type="user",
        resource_id=target.id,
        user_id=user.id,
        details=body.model_dump(exclude_none=True),
    )
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/status")
async def system_status(
    user: CurrentUser = Depends(RequireRole("administrator")),
    db: AsyncSession = Depends(get_db),
):
    user_count = await db.execute(select(func.count(User.id)))
    doc_count = await db.execute(select(func.count(Document.id)))
    pending = await db.execute(
        select(func.count(Document.id)).where(Document.status == "pending_classification")
    )

    return {
        "total_users": user_count.scalar() or 0,
        "total_documents": doc_count.scalar() or 0,
        "pending_classification": pending.scalar() or 0,
    }
