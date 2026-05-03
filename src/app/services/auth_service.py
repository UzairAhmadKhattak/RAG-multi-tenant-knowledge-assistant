from src.app.models import User
from src.app.core.security import verify_password, create_token
from src.app.core.constants import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, id: str):
    result = await db.execute(
        select(User).where(User.id == int(id))
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

    access_token = create_token({"sub": str(user.id),"type":"access_token"},
                                ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_token({"sub": str(user.id),"type":"refresh_token"},
                                 REFRESH_TOKEN_EXPIRE_MINUTES)

    return {
        "username": user.username,
        "role": user.role,
        "organization_id": user.organization_id,
        "created_at": user.created_at,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }