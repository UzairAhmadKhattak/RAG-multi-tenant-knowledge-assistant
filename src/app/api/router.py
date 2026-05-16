from fastapi import APIRouter
from .v1.auth import auth_router
from .v1.documents import doc_router
from .v1.chat import chat_router

api_router = APIRouter()

api_router.include_router(auth_router,prefix="/auth",tags=['Auth'])
api_router.include_router(doc_router,prefix="/docs",tags=['Documents'])
api_router.include_router(chat_router,prefix="/chat",tags=['Chat'])