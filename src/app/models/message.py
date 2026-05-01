from base import Base
from sqlalchemy import Integer, DateTime,ForeignKey,func,Text,Enum
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from datetime import datetime
import enum

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"

class Message(Base):

    __table__ = "messages"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    content: Mapped[int] = mapped_column(Text,nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole),
                                              nullable=False,
                                              default=MessageRole.user)
    token_count: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))

    conversation = Relationship("Conversation",back_populates="messages")