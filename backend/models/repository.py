from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.user import GUID
import uuid

# 저장소 테이블
class Repository(Base):
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
    owner = relationship("User", back_populates="repositories")
    members = relationship("RepositoryMember", back_populates="repository")
    chat_rooms = relationship("ChatRoom", back_populates="repository")
    vector_collections = relationship("VectorCollection", back_populates="repository")

# 저장소 멤버 테이블
class RepositoryMember(Base):
    __tablename__ = "repository_members"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repository_id = Column(GUID(), ForeignKey("repositories.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member, viewer
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    repository = relationship("Repository", back_populates="members")
    user = relationship("User", back_populates="repository_members")