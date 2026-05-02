import asyncio
from src.app.db.session import AsyncSessionLocal, engine
from src.app.models import User, Organization
from src.app.core.security import hash_password
from src.app.models.base import Base

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Create organization first
        org = Organization(
            name="Test Org"
        )
        db.add(org)
        await db.flush()  # ensures org.id is available

        # 2. Create user with organization_id
        user = User(
            username="test@example.com",
            password=hash_password("1234"),
            organization_id=org.id
        )

        db.add(user)

        await db.commit()

    print("Organization and User created")

asyncio.run(seed())