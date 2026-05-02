from fastapi import APIRouter,Depends,HTTPException
from src.app.schemas.user import UserLoginRequest, UserLoginResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.session import get_db
from src.app.services.auth_service import login_user

auth_router = APIRouter()
@auth_router.post("/login")
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await login_user(db, payload.username, payload.password)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return result