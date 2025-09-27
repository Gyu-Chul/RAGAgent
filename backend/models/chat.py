from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.user import GUID
import uuid

# 채팅룸 테이블
class ChatRoom(Base):
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
    repository = relationship("Repository", back_populates="chat_rooms")
    messages = relationship("ChatMessage", back_populates="chat_room")

# 채팅 메시지 테이블
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(GUID(), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # None for bot messages
    sender_type = Column(String(10), default="user")  # user, bot
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string of source files
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="messages")