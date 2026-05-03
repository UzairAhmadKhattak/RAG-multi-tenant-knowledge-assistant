

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector


def load_pdf_file(file_path:str):
    loader = PyPDFLoader(file_path)
    return loader.load()

def load_text_file(file_path:str):
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()

def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(docs)


async def embed_file(file_path: str):
    pass