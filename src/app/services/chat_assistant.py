
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.document_chunk import DocumentChunk
from src.app.services.embed import embed_query
from src.app.core.constants import ROLE_ACCESS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.app.models.document import Document
from typing import List
import time
from src.app.models.message import Message

async def get_documents(db:AsyncSession,document_ids:List[int]) -> dict:
    documents = await db.execute(
        select(Document).where(Document.id.in_(document_ids)).order_by(Document.id)
        )
    documents_dict = {doc.id:doc for doc in documents.scalars().all()}
    return documents_dict

def build_context(chunks,document_dict:dict):
    formatted_context = []

    for chunk in chunks:
        doc = document_dict[chunk.document_id]

        formatted_context.append(
            f"""
            Document Title:
            {doc.title}

            Document Summary:
            {doc.summary}

            Relevant Chunk:
            {chunk.content}
            """
                )

    context = "\n\n====================\n\n".join(formatted_context)
    return context

async def search_vectors(db, organization_id, role, embedded_query):
    role_key = role.value if hasattr(role, "value") else role
    allowed_levels = ROLE_ACCESS[role_key]

    access_match = or_(
        *(
            DocumentChunk.meta_data["access_level"].contains([level])
            for level in allowed_levels
        )
    )

    stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.organization_id == organization_id,
            access_match,
        )
        .order_by(DocumentChunk.embedding.cosine_distance(embedded_query))
        .limit(5)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def llm_response(context, chat_history_summary, last_messages, query):

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chat_history = "\n\n".join([f"User query: {message.user_query} \n Assistant Response: {message.assistant_response}" for  message in last_messages])

    prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a helpful assistant. 
        Answer using the provided context and to understand the overall meaning and purpose of the documents use the documents summary.
        Use the chat history summary to understand the overall meaning and purpose of the chat.
        The context may be messy or have formatting issues — extract relevant information regardless.
        Only say you don't know if the topic is genuinely absent."""),
    ("user",
     """Context:
        {context}
        Chat history summary:
        {chat_history_summary}
        Chat history:
        {chat_history}
        Question:
        {question}
     """)
    ])

    chain = prompt | llm

    start_time = time.perf_counter()

    response = await chain.ainvoke({
        "context": context,
        "chat_history_summary": chat_history_summary,
        "chat_history": chat_history,
        "question": query
    })

    latency_ms = (time.perf_counter() - start_time) * 1000

    # ---- token usage extraction (robust) ----
    usage = getattr(response, "usage_metadata", None) or {}

    prompt_tokens = usage.get("input_tokens")
    completion_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")

    # fallback for older/alternate metadata formats
    if not total_tokens:
        usage2 = getattr(response, "response_metadata", {}).get("token_usage", {})
        prompt_tokens = prompt_tokens or usage2.get("prompt_tokens")
        completion_tokens = completion_tokens or usage2.get("completion_tokens")
        total_tokens = total_tokens or usage2.get("total_tokens")

    # ---- cost estimation (you should adjust pricing as needed) ----
    # Example placeholder rates for gpt-4o-mini (update based on your billing)
    INPUT_COST_PER_1K = 0.00015
    OUTPUT_COST_PER_1K = 0.00060

    cost = None
    if prompt_tokens is not None and completion_tokens is not None:
        cost = (
            (prompt_tokens / 1000) * INPUT_COST_PER_1K +
            (completion_tokens / 1000) * OUTPUT_COST_PER_1K
        )

    return {
        "response_content": response.content,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "cost": cost
    }

async def get_answer(db:AsyncSession,organization_id:int,role,query:str,chat_history_summary:str,last_messages:List[Message]):
    
    embedded_query = await embed_query(query)
    chunks = await search_vectors(db,organization_id,role,embedded_query)
    document_ids = list(set(chunk.document_id for chunk in chunks))
    document_dict = await get_documents(db, document_ids)
    context = build_context(chunks,document_dict)

    return await llm_response(context,chat_history_summary,last_messages,query)
    


