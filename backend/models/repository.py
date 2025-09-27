"""
저장소 모델 정의
단일 책임: 저장소 및 저장소 멤버 관련 데이터베이스 모델만 담당
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from core.database import Base
from models.types import GUID

if TYPE_CHECKING:
    from models.user import User
    from models.chat import ChatRoom
    from models.vector import VectorCollection

class Repository(Base):
    """저장소 모델"""
    __tablename__ = "repositories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(255))
    owner_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    stars = Column(Integer, default=0)
    language = Column(String(50))
    status = Column(String(20), default="active")  # active, syncing, error
    vectordb_status = Column(String(20), default="pending")  # pending, healthy, syncing, error
    collections_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))

    # 관계 설정
    owner: Mapped["User"] = relationship("User", back_populates="repositories")
    members: Mapped[List["RepositoryMember"]] = relationship("RepositoryMember", back_populates="repository")
    chat_rooms: Mapped[List["ChatRoom"]] = relationship("ChatRoom", back_populates="repository")
    vector_collections: Mapped[List["VectorCollection"]] = relationship("VectorCollection", back_populates="repository")

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, name={self.name}, owner_id={self.owner_id})>"

class RepositoryMember(Base):
    """저장소 멤버 모델"""
    __tablename__ = "repository_members"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repository_id = Column(GUID(), ForeignKey("repositories.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member, viewer
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    repository: Mapped["Repository"] = relationship("Repository", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="repository_members")

    def __repr__(self) -> str:
        return f"<RepositoryMember(id={self.id}, repository_id={self.repository_id}, user_id={self.user_id}, role={self.role})>"