
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import HTTPException
from langchain_openai import OpenAIEmbeddings
from src.app.models.document_chunk import DocumentChunk
from src.app.core.constants import BUFFER_SIZE
from odf.opendocument import load as load_odt
from odf.text import P
from langchain_core.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession


async def load_pdf_file(file_path: str):
    loader = PyPDFLoader(file_path)
    return loader.alazy_load()


async def load_text_file(file_path: str):
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.alazy_load()


async def load_docx_file(file_path: str):
    # Docx2txtLoader doesn't support async lazy loading, wrap it to match the interface
    loader = Docx2txtLoader(file_path)
    async def _gen():
        for doc in loader.load():
            yield doc
    return _gen()

async def load_odt_file(file_path: str):
    odt_doc = load_odt(file_path)
    paragraphs = odt_doc.text.getElementsByType(P)
    full_text = "\n".join(
        "".join(node.data for node in p.childNodes if hasattr(node, "data"))
        for p in paragraphs
    )
    async def _gen():
        yield Document(page_content=full_text, metadata={"source": file_path})
    return _gen()

MIME_TYPE_LOADERS = {
    "text/plain": load_text_file,
    "application/pdf": load_pdf_file,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": load_docx_file,
    "application/vnd.oasis.opendocument.text": load_odt_file,
}


def split_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(docs)


async def embed_documents(documents: list) -> list:
    # embed_documents expects plain strings, so extract page_content from each Document
    texts = [doc.page_content for doc in documents]
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    return await embedder.aembed_documents(texts)


async def flush_buffer(
    db:AsyncSession,
    docs_buffer: list,
    organization_id: int,
    document_id: int,
) -> None:
    """Split, embed, and persist a batch of raw Documents."""
    if not docs_buffer:
        return

    split_docs = split_documents(docs_buffer)
    if not split_docs:
        return

    embeddings = await embed_documents(split_docs)

    for chunk, embedding in zip(split_docs, embeddings):
        document_chunk = DocumentChunk(
            organization_id=organization_id,
            document_id=document_id,
            content=chunk.page_content,
            embedding=embedding,
            meta_data=chunk.metadata,
        )
        db.add(document_chunk)


async def embed_file(
    db:AsyncSession,
    file_path: str,
    mime_type: str,
    organization_id: int,
    document_id: int,
) -> None:
    if mime_type not in MIME_TYPE_LOADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime_type}",
        )

    file_loader = MIME_TYPE_LOADERS[mime_type]
    docs_stream = await file_loader(file_path)

    docs_buffer = []

    async for doc in docs_stream:
        docs_buffer.append(doc)

        if len(docs_buffer) >= BUFFER_SIZE:
            await flush_buffer(db,docs_buffer, organization_id, document_id)
            docs_buffer = []

    # Flush any remaining docs that didn't fill a full buffer
    await flush_buffer(db,docs_buffer, organization_id, document_id)