from .base import Base
from sqlalchemy import String, Integer, DateTime,ForeignKey,func,Text
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from datetime import datetime


class Document(Base):

    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(255),
                                          nullable=False,
                                          unique=True)
    file_path:Mapped[str] = mapped_column(String(255),nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    summary: Mapped[str] = mapped_column(Text,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())


    uploaded_by = Relationship("User",back_populates='documents')
    doc_org = Relationship("Organization",back_populates='org_docs')
    document_chunks = Relationship('DocumentChunk',back_populates='document')