from .base import Base
from sqlalchemy import String, Integer, DateTime,ForeignKey,func,Text,Enum,Numeric
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from datetime import datetime
from decimal import Decimal
import enum



class QueryLog(Base):

    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    prompt_tokens: Mapped[int] = mapped_column(Integer,nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer,nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer,nullable=False)
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(10,2),nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(3,2),nullable=False)
     
    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())

    message = Relationship("Message",back_populates="message_query_log")
