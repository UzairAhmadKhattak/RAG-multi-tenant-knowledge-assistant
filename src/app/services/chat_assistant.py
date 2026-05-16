
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.document_chunk import DocumentChunk
from src.app.services.embed import embed_query
from src.app.core.constants import ROLE_ACCESS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

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

async def llm_response(context, query):

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant. Answer using the provided context. "
     "The context may be messy or have formatting issues — extract relevant information regardless. "
     "Only say you don't know if the topic is genuinely absent."),
    ("user",
     "Context:\n{context}\n\nQuestion: {question}")
    ])

    chain = prompt | llm

    response = await chain.ainvoke({
        "context": context,
        "question": query
    })

    return response.content

async def get_answer(db:AsyncSession,organization_id:int,role,query:str):
    
    embedded_query = await embed_query(query)
    chunks = await search_vectors(db,organization_id,role,embedded_query)
    context = "\n\n".join(
            [chunk.content for chunk in chunks]
        )
    return await llm_response(context,query)
    


