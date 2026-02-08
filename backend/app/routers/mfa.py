import io

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.user import User
from app.services import audit_service

router = APIRouter(prefix="/api/auth/mfa", tags=["mfa"])


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    code: str


@router.post("/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()

    if db_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")

    secret = pyotp.random_base32()
    db_user.mfa_secret = secret
    await db.commit()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=db_user.email, issuer_name="CRDP"
    )
    return MfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.get("/qr")
async def get_qr_code(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()

    if not db_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up. Call /setup first.")

    uri = pyotp.totp.TOTP(db_user.mfa_secret).provisioning_uri(
        name=db_user.email, issuer_name="CRDP"
    )

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.post("/verify")
async def verify_mfa(
    body: MfaVerifyRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()

    if not db_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up")

    totp = pyotp.TOTP(db_user.mfa_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    db_user.mfa_enabled = True
    await db.flush()

    await audit_service.log_action(
        db,
        action="mfa_enabled",
        resource_type="user",
        resource_id=db_user.id,
        user_id=db_user.id,
    )
    await db.commit()

    return {"message": "MFA enabled successfully"}
