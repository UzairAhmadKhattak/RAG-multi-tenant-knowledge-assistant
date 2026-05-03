from fastapi import APIRouter,Depends,HTTPException
from src.app.schemas.user import UserLoginResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.session import get_db
from src.app.services.auth_service import login_user
from fastapi.security import OAuth2PasswordRequestForm

auth_router = APIRouter()
@auth_router.post("/login",response_model=UserLoginResponse)
async def login(payload: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await login_user(db, payload.username, payload.password)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return result