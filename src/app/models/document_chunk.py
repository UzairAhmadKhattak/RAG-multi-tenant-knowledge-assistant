from base import Base
from sqlalchemy import Integer,ForeignKey,Text,JSONB
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from pgvector.sqlalchemy import Vector

class DocumentChunk(Base):
    id: Mapped[int] = mapped_column(Integer,primary_key=True)

    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'))

    content: Mapped[str] = mapped_column(Text,nullable=False)
    embedding:Mapped[list[float]] = mapped_column(Vector(1536))
    meta_data: Mapped[dict] = mapped_column(JSONB)
    
    document = Relationship("User",back_populates='document_chunks')