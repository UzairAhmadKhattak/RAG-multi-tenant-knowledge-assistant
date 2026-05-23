from .base import Base
from sqlalchemy import String, Integer, DateTime,ForeignKey,func,Text,Enum
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from datetime import datetime


class Conversation(Base):

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    summary: Mapped[str] = mapped_column(Text,nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())

    user = Relationship("User",back_populates="conversations")
    messages = Relationship("Message",back_populates="conversation")