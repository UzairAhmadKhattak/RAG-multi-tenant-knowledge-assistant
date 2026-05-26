from fastapi import APIRouter,Depends
from src.app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.api.deps import get_current_user
from src.app.services.chat_assistant import get_answer
from src.app.models.user import User
from src.app.models.conversation import Conversation
from src.app.models.message import Message
from src.app.models.query_log import QueryLog
from src.app.utils.query_helpers import get_or_create
from sqlalchemy import select
from src.app.services.summarizer import summarize_chat
chat_router = APIRouter()

@chat_router.post("/")
async def chat(query:str,
               conversation_id:int|None = None,                     
               db: AsyncSession = Depends(get_db),
               user: User = Depends(get_current_user)
    ):
    
    organization_id = user.organization_id
    user_role = user.role
    user_id = user.id

    conversation,_ = await get_or_create(db,
                Conversation,
                id=conversation_id,
                defaults={"title":query[:200],"summary":None,"user_id":user_id,"organization_id":organization_id}
                )
    # get last 10 messages
    messages = await db.execute(select(Message).where(Message.conversation_id==conversation.id).order_by(Message.id.desc()).limit(10))
    messages = messages.scalars().all()

    if len(messages) == 10:
        # create summary of last 10 messages
        chat_history_summary = await summarize_chat(messages)
        conversation.summary = chat_history_summary
        db.add(conversation)
        await db.flush()
    else:
        chat_history_summary = conversation.summary if conversation.summary else ""

    response = await get_answer(
        db,
        organization_id,
        user_role,
        query,
        chat_history_summary,
        messages
    )

    message = Message(user_query=query,
                      assistant_response=response['response_content'],
                      conversation_id=conversation.id)
    db.add(message)
    await db.flush()
    query_log = QueryLog(organization_id=organization_id,
             message_id=message.id,
             prompt_tokens=response['prompt_tokens'],
             completion_tokens=response['completion_tokens'],
             total_tokens=response['total_tokens'],
             latency_ms=response['latency_ms'],
             cost=response['cost'])
    query_log = db.add(query_log)
    await db.flush()
    await db.commit()
    return {"response": response['response_content'],"conversation_id":conversation.id}