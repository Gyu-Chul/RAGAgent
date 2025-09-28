"""
사용자 세션 모델 정의
단일 책임: 사용자 세션 관련 데이터베이스 모델만 담당
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from ..core.database import Base
from .types import GUID

if TYPE_CHECKING:
    from .user import User


class UserSession(Base):
    """사용자 세션 모델 - JWT 토큰 관리"""
    __tablename__ = "user_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(512), unique=True, nullable=False, index=True)  # JWT 토큰
    refresh_token = Column(String(512), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"