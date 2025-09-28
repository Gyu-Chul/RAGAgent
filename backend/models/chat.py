"""
채팅 모델 정의
단일 책임: 채팅룸 및 채팅 메시지 관련 데이터베이스 모델만 담당
"""

import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from ..core.database import Base
from .types import GUID

if TYPE_CHECKING:
    from .repository import Repository
    from .user import User


class ChatRoom(Base):
    """채팅룸 모델"""
    __tablename__ = "chat_rooms"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    repository_id = Column(GUID(), ForeignKey("repositories.id"), nullable=False)
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    message_count = Column(Integer, default=0)
    last_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    repository: Mapped["Repository"] = relationship("Repository", back_populates="chat_rooms")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="chat_room", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChatRoom(id={self.id}, name={self.name}, repository_id={self.repository_id})>"


class ChatMessage(Base):
    """채팅 메시지 모델"""
    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(GUID(), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # None for bot messages
    sender_type = Column(String(10), default="user")  # user, bot
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string of source files
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    chat_room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")
    sender: Mapped[Optional["User"]] = relationship("User", foreign_keys=[sender_id])

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, chat_room_id={self.chat_room_id}, sender_type={self.sender_type})>"