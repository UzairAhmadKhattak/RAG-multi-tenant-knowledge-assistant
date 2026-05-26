from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.app.models.message import Message
from typing import List

async def summaries_document(file):

    file.file.seek(0)

    raw_content = await file.read(1024 * 1024)

    # If it's bytes, decode safely
    text = raw_content.decode("utf-8", errors="ignore")

    # ---- STEP 1: split into pages (simple heuristic) ----
    # This assumes pages are separated by form feed or large breaks
    pages = text.split("\f") if "\f" in text else text.split("\n\n\n")

    if len(pages) == 0:
        pages = [text]

    # ---- STEP 2: pick first, middle, last ----
    first_page = pages[0]
    middle_page = pages[len(pages) // 2]
    last_page = pages[-1]

    selected_content = f"""
    FIRST PAGE:
    {first_page}

    MIDDLE PAGE:
    {middle_page}

    LAST PAGE:
    {last_page}
    """

    # ---- STEP 3: LLM ----
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
    You are a document summarizer.

    Summarize the document using the provided excerpts:
    - first page (introduction/context)
    - middle page (main content)
    - last page (conclusion/summary if present)

    Produce one clear paragraph summarizing the full document meaning.
    Ignore formatting noise.
    """
            ),
            (
                "user",
                """
    DOCUMENT EXCERPTS:
    {content}
    """
            )
        ])

    chain = prompt | llm

    response = await chain.ainvoke({
        "content": selected_content
    })

    return response.content


async def summarize_chat(messages:List[Message]) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    chat_history = "\n\n".join([f"User query: {message.user_query} \n Assistant Response: {message.assistant_response}" for  message in messages])

    prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a chat summarizer.

                Summarize the chat using the provided messages:
                - last 10 messages

                Produce one clear paragraph summarizing the full chat meaning.
                Ignore formatting noise.
                """
                ),
                (
                    "user",
                    """
                    CHAT HISTORY:
                    {chat_history}
                    """
                )
        ])

    chain = prompt | llm

    response = await chain.ainvoke({
        "chat_history": chat_history
    })

    return response.content