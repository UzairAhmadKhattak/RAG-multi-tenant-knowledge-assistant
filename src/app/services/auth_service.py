from src.app.models import User
from src.app.core.security import verify_password, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user


async def login_user(db: AsyncSession, username: str, password: str):
    user = await authenticate_user(db, username, password)

    if not user:
        return None

    token = create_access_token({"sub": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }