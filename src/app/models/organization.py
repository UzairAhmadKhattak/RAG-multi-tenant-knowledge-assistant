
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from sqlalchemy import String,Integer

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    name: Mapped[str] = mapped_column(String(255),nullable=False)

    users = Relationship('User',back_populates='organization')
    org_docs = Relationship("Document",back_populates="doc_org")