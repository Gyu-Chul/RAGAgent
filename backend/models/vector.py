"""
벡터 데이터베이스 모델 정의
단일 책임: 벡터 컬렉션 관련 데이터베이스 모델만 담당
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from ..core.database import Base
from .types import GUID

if TYPE_CHECKING:
    from .repository import Repository


class VectorCollection(Base):
    """벡터 컬렉션 모델"""
    __tablename__ = "vector_collections"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    repository_id = Column(GUID(), ForeignKey("repositories.id"), nullable=False)
    description = Column(Text)
    entity_count = Column(Integer, default=0)
    dimension = Column(Integer, default=768)
    index_type = Column(String(20), default="HNSW")
    status = Column(String(20), default="pending")  # pending, ready, syncing, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    repository: Mapped["Repository"] = relationship("Repository", back_populates="vector_collections")

    def __repr__(self) -> str:
        return f"<VectorCollection(id={self.id}, name={self.name}, repository_id={self.repository_id}, status={self.status})>"