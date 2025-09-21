from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# 사용자 관련 스키마
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# 토큰 관련 스키마
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None

# 세션 관련 스키마
class SessionResponse(BaseModel):
    id: UUID
    session_token: str
    expires_at: datetime
    is_active: bool
    last_activity: datetime

    class Config:
        from_attributes = True

# 저장소 관련 스키마
class RepositoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryResponse(RepositoryBase):
    id: UUID
    owner_id: UUID
    stars: int
    language: Optional[str]
    status: str
    vectordb_status: str
    collections_count: int
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_sync: Optional[datetime]

    class Config:
        from_attributes = True

# 저장소 멤버 관련 스키마
class RepositoryMemberResponse(BaseModel):
    id: UUID
    repository_id: UUID
    user_id: UUID
    username: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

# 채팅룸 관련 스키마
class ChatRoomBase(BaseModel):
    name: str

class ChatRoomCreate(ChatRoomBase):
    repository_id: UUID

class ChatRoomResponse(ChatRoomBase):
    id: UUID
    repository_id: UUID
    created_by: UUID
    message_count: int
    last_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 채팅 메시지 관련 스키마
class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    chat_room_id: UUID
    sender_type: str = "user"

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    chat_room_id: UUID
    sender_id: Optional[UUID]
    sender_type: str
    sources: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 벡터 컬렉션 관련 스키마
class VectorCollectionResponse(BaseModel):
    id: UUID
    name: str
    repository_id: UUID
    description: Optional[str]
    entity_count: int
    dimension: int
    index_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# API 응답 스키마
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class LoginResponse(BaseModel):
    success: bool
    user: UserResponse
    token: Token
    message: str = "Login successful"