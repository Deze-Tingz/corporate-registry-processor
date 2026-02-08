"""Seed an initial administrator user.

Usage:
    python -m app.scripts.seed_admin
"""

import asyncio

from sqlalchemy import select

from app.database import async_session, engine
from app.models import Base
from app.models.user import User
from app.utils.hashing import hash_password

ADMIN_EMAIL = "admin@bvifsc.vg"
ADMIN_NAME = "System Administrator"
ADMIN_PASSWORD = "ChangeMe123!"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if result.scalar_one_or_none():
            print(f"Admin user {ADMIN_EMAIL} already exists.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="administrator",
        )
        db.add(admin)
        await db.commit()
        print(f"Created admin user: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("IMPORTANT: Change this password immediately after first login.")


if __name__ == "__main__":
    asyncio.run(seed())
