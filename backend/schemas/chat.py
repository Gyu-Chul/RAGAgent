"""
Chat 스키마 정의
단일 책임: API 요청/응답을 위한 데이터 검증 및 직렬화
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ChatRoom Schemas

class ChatRoomBase(BaseModel):
    """ChatRoom 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)


class ChatRoomCreate(ChatRoomBase):
    """ChatRoom 생성 스키마"""
    repository_id: str


class ChatRoomUpdate(BaseModel):
    """ChatRoom 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ChatRoomResponse(ChatRoomBase):
    """ChatRoom 응답 스키마"""
    id: str
    repository_id: str
    created_by: str
    message_count: int = 0
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ChatMessage Schemas

class ChatMessageBase(BaseModel):
    """ChatMessage 기본 스키마"""
    content: str = Field(..., min_length=1)


class ChatMessageCreate(ChatMessageBase):
    """ChatMessage 생성 스키마"""
    chat_room_id: str
    sender_type: str = "user"  # user, bot
    sources: Optional[str] = None


class ChatMessageResponse(ChatMessageBase):
    """ChatMessage 응답 스키마"""
    id: str
    chat_room_id: str
    sender_id: Optional[str] = None
    sender_type: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
