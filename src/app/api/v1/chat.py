from fastapi import APIRouter,Depends
from src.app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.api.deps import get_current_user
from src.app.services.chat_assistant import get_answer
from src.app.models.user import User

chat_router = APIRouter()

@chat_router.post("/")
async def chat(query:str,                      
               db: AsyncSession = Depends(get_db),
               user: User = Depends(get_current_user)
    ):
    
    organization_id = user.organization_id
    user_role = user.role
    response = await get_answer(
        db,
        organization_id,
        user_role,
        query
    )
    return {"response": response}