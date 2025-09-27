from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.user import GUID
import uuid

# 벡터 컬렉션 테이블
class VectorCollection(Base):
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
    repository = relationship("Repository", back_populates="vector_collections")