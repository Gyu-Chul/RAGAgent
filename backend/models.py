from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, CHAR
from database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if not isinstance(value, uuid.UUID) else value
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value

# 사용자 테이블
class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="owner")
    repository_members = relationship("RepositoryMember", back_populates="user")

# 사용자 세션 테이블 (JWT 토큰 관리)
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="sessions")

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

# 채팅룸 테이블
class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    repository_id = Column(GUID(), ForeignKey("repositories.id"), nullable=False)
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    message_count = Column(Integer, default=0)
    last_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    repository = relationship("Repository", back_populates="chat_rooms")
    messages = relationship("ChatMessage", back_populates="chat_room")

# 채팅 메시지 테이블
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(GUID(), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # None for bot messages
    sender_type = Column(String(10), default="user")  # user, bot
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string of source files
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="messages")

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