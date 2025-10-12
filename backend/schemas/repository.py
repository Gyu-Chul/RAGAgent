"""
Repository 스키마 정의
단일 책임: API 요청/응답을 위한 데이터 검증 및 직렬화
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

# Repository Schemas

class RepositoryBase(BaseModel):
    """Repository 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    url: str = Field(..., description="Git repository URL")
    is_public: bool = False


class RepositoryCreate(RepositoryBase):
    """Repository 생성 스키마"""
    pass


class RepositoryUpdate(BaseModel):
    """Repository 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class RepositoryResponse(RepositoryBase):
    """Repository 응답 스키마"""
    id: str
    owner_id: str
    owner: Optional[str] = None  # owner username
    stars: int = 0
    language: Optional[str] = None
    status: str
    vectordb_status: str
    error_message: Optional[str] = None  # 에러 발생 시 상세 메시지
    collections_count: int = 0
    file_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True


# Repository Member Schemas

class RepositoryMemberBase(BaseModel):
    """Repository Member 기본 스키마"""
    user_id: str
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")


class RepositoryMemberCreate(RepositoryMemberBase):
    """Repository Member 생성 스키마"""
    pass


class RepositoryMemberUpdate(BaseModel):
    """Repository Member 업데이트 스키마"""
    role: str = Field(..., pattern="^(admin|member|viewer)$")


class RepositoryMemberResponse(RepositoryMemberBase):
    """Repository Member 응답 스키마"""
    id: str
    repository_id: str
    joined_at: datetime
    username: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class RepositoryWithMembers(RepositoryResponse):
    """멤버 정보를 포함한 Repository 응답"""
    members: List[RepositoryMemberResponse] = []

    class Config:
        from_attributes = True
