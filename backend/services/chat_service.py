"""
Chat 서비스
단일 책임: Chat 비즈니스 로직 처리
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..models.chat import ChatRoom, ChatMessage
from ..schemas.chat import (
    ChatRoomCreate,
    ChatRoomUpdate,
    ChatMessageCreate
)


class ChatRoomService:
    """ChatRoom 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_chat_room(
        db: Session,
        room_data: ChatRoomCreate,
        user_id: str
    ) -> ChatRoom:
        """
        새로운 ChatRoom 생성

        Args:
            db: 데이터베이스 세션
            room_data: ChatRoom 생성 데이터
            user_id: 생성자 ID

        Returns:
            생성된 ChatRoom 객체
        """
        db_chat_room = ChatRoom(
            id=uuid.uuid4(),
            name=room_data.name,
            repository_id=uuid.UUID(room_data.repository_id),
            created_by=uuid.UUID(user_id),
            message_count=0
        )

        db.add(db_chat_room)
        db.commit()
        db.refresh(db_chat_room)

        return db_chat_room

    @staticmethod
    def get_chat_room(db: Session, room_id: str) -> Optional[ChatRoom]:
        """ChatRoom 조회"""
        return db.query(ChatRoom).filter(ChatRoom.id == uuid.UUID(room_id)).first()

    @staticmethod
    def get_repository_chat_rooms(db: Session, repo_id: str) -> List[ChatRoom]:
        """Repository의 모든 ChatRoom 조회"""
        return db.query(ChatRoom).filter(
            ChatRoom.repository_id == uuid.UUID(repo_id)
        ).order_by(ChatRoom.updated_at.desc()).all()

    @staticmethod
    def update_chat_room(
        db: Session,
        room_id: str,
        room_data: ChatRoomUpdate
    ) -> Optional[ChatRoom]:
        """ChatRoom 업데이트"""
        db_chat_room = ChatRoomService.get_chat_room(db, room_id)
        if not db_chat_room:
            return None

        update_data = room_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_chat_room, field, value)

        db_chat_room.updated_at = datetime.now()
        db.commit()
        db.refresh(db_chat_room)

        return db_chat_room

    @staticmethod
    def delete_chat_room(db: Session, room_id: str) -> bool:
        """ChatRoom 삭제"""
        db_chat_room = ChatRoomService.get_chat_room(db, room_id)
        if not db_chat_room:
            return False

        db.delete(db_chat_room)
        db.commit()
        return True

    @staticmethod
    def update_last_message(
        db: Session,
        room_id: str,
        message_content: str
    ) -> Optional[ChatRoom]:
        """ChatRoom의 마지막 메시지 업데이트"""
        db_chat_room = ChatRoomService.get_chat_room(db, room_id)
        if not db_chat_room:
            return None

        db_chat_room.last_message = message_content
        db_chat_room.message_count = (db_chat_room.message_count or 0) + 1
        db_chat_room.updated_at = datetime.now()
        db.commit()
        db.refresh(db_chat_room)

        return db_chat_room


class ChatMessageService:
    """ChatMessage 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_message(
        db: Session,
        message_data: ChatMessageCreate,
        user_id: Optional[str] = None
    ) -> ChatMessage:
        """
        새로운 ChatMessage 생성

        Args:
            db: 데이터베이스 세션
            message_data: ChatMessage 생성 데이터
            user_id: 발신자 ID (bot 메시지의 경우 None)

        Returns:
            생성된 ChatMessage 객체
        """
        db_message = ChatMessage(
            id=uuid.uuid4(),
            chat_room_id=uuid.UUID(message_data.chat_room_id),
            sender_id=uuid.UUID(user_id) if user_id else None,
            sender_type=message_data.sender_type,
            content=message_data.content,
            sources=message_data.sources
        )

        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # ChatRoom의 마지막 메시지 업데이트
        ChatRoomService.update_last_message(
            db,
            message_data.chat_room_id,
            message_data.content
        )

        return db_message

    @staticmethod
    def get_message(db: Session, message_id: str) -> Optional[ChatMessage]:
        """ChatMessage 조회"""
        return db.query(ChatMessage).filter(
            ChatMessage.id == uuid.UUID(message_id)
        ).first()

    @staticmethod
    def get_chat_room_messages(db: Session, room_id: str) -> List[ChatMessage]:
        """ChatRoom의 모든 메시지 조회"""
        return db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == uuid.UUID(room_id)
        ).order_by(ChatMessage.created_at.asc()).all()

    @staticmethod
    def delete_message(db: Session, message_id: str) -> bool:
        """ChatMessage 삭제"""
        db_message = ChatMessageService.get_message(db, message_id)
        if not db_message:
            return False

        db.delete(db_message)
        db.commit()
        return True
