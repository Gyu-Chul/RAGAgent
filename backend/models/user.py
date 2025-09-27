"""
사용자 모델 정의
단일 책임: 사용자 관련 데이터베이스 모델만 담당
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from core.database import Base
from models.types import GUID

if TYPE_CHECKING:
    from models.repository import Repository, RepositoryMember
    from models.session import UserSession


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    repositories: Mapped[List["Repository"]] = relationship("Repository", back_populates="owner")
    repository_members: Mapped[List["RepositoryMember"]] = relationship("RepositoryMember", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"