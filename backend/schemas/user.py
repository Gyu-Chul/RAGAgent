from pydantic import BaseModel, EmailStr
from typing import Optional
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