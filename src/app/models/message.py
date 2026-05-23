from .base import Base
from sqlalchemy import Integer, DateTime,ForeignKey,func,Text,Enum
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from datetime import datetime
import enum


class Message(Base):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_query: Mapped[str] = mapped_column(Text,nullable=False)
    assistant_response: Mapped[str] = mapped_column(Text,nullable=False)
    
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))

    conversation = Relationship("Conversation",back_populates="messages")
    message_query_log = Relationship("QueryLog",back_populates="message")