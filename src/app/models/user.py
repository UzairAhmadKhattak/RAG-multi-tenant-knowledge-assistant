from .base import Base
from sqlalchemy import String, Integer, DateTime,Enum,ForeignKey,func
from sqlalchemy.orm import Mapped, mapped_column, Relationship
import enum
from datetime import datetime


class UserRole(str,enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    username: Mapped[str] = mapped_column(String(255),
                                          nullable=False,
                                          index=True,unique=True)
    password:Mapped[str] = mapped_column(String(255),nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole),default=UserRole.employee,
                                           nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime,server_default=func.now())

    organization = Relationship("Organization", back_populates='users')
    documents = Relationship("Document", back_populates='uploaded_by')
    conversations = Relationship("Conversation",back_populates='user')
