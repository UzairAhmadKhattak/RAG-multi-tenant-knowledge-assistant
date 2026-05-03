import asyncio
from sqlalchemy import select

from src.app.db.session import AsyncSessionLocal, engine
from src.app.models import User, Organization,UserRole
from src.app.core.security import hash_password
from src.app.models.base import Base


async def seed():
    ORGANIZATION_NAME = "Test Org"
    USERNAME = "test"
    PASSWORD = "1234"
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:

        # 🔹 1. Check if organization exists
        org_result = await db.execute(
            select(Organization).where(Organization.name == ORGANIZATION_NAME)
        )
        org = org_result.scalar_one_or_none()

        if not org:
            org = Organization(name=ORGANIZATION_NAME)
            db.add(org)
            await db.flush()  # get org.id
            print("Organization created")
        else:
            print("Organization already exists")

        # 🔹 2. Check if user exists
        user_result = await db.execute(
            select(User).where(User.username == USERNAME)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            user = User(
                username=USERNAME,
                password=hash_password(PASSWORD),
                organization_id=org.id,
                role=UserRole.admin
            )
            db.add(user)
            print("User created")
        else:
            print("User already exists")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())