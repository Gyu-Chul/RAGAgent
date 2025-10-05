"""
Database Helper for RAG Worker
backend 모듈 의존성 없이 직접 DB 업데이트를 수행
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import uuid


class RepositoryDBHelper:
    """Repository DB 직접 업데이트를 위한 헬퍼 클래스"""

    @staticmethod
    def update_repository_status(
        db: Session,
        repo_id: str,
        status: str,
        vectordb_status: Optional[str] = None
    ) -> bool:
        """
        Repository 상태 업데이트

        Args:
            db: 데이터베이스 세션
            repo_id: Repository ID (UUID string)
            status: Repository status
            vectordb_status: VectorDB status (optional)

        Returns:
            성공 여부
        """
        try:
            repo_uuid = uuid.UUID(repo_id)
            now = datetime.now()

            if vectordb_status:
                query = text("""
                    UPDATE repositories
                    SET status = :status,
                        vectordb_status = :vectordb_status,
                        last_sync = :last_sync
                    WHERE id = :repo_id
                """)
                db.execute(query, {
                    "status": status,
                    "vectordb_status": vectordb_status,
                    "last_sync": now,
                    "repo_id": repo_uuid
                })
            else:
                query = text("""
                    UPDATE repositories
                    SET status = :status,
                        last_sync = :last_sync
                    WHERE id = :repo_id
                """)
                db.execute(query, {
                    "status": status,
                    "last_sync": now,
                    "repo_id": repo_uuid
                })

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_file_count(db: Session, repo_id: str, file_count: int) -> bool:
        """
        파일 개수 업데이트

        Args:
            db: 데이터베이스 세션
            repo_id: Repository ID (UUID string)
            file_count: 파일 개수

        Returns:
            성공 여부
        """
        try:
            repo_uuid = uuid.UUID(repo_id)

            query = text("""
                UPDATE repositories
                SET file_count = :file_count
                WHERE id = :repo_id
            """)
            db.execute(query, {
                "file_count": file_count,
                "repo_id": repo_uuid
            })

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def increment_collections_count(db: Session, repo_id: str) -> bool:
        """
        Collections count 1 증가

        Args:
            db: 데이터베이스 세션
            repo_id: Repository ID (UUID string)

        Returns:
            성공 여부
        """
        try:
            repo_uuid = uuid.UUID(repo_id)

            query = text("""
                UPDATE repositories
                SET collections_count = collections_count + 1
                WHERE id = :repo_id
            """)
            db.execute(query, {
                "repo_id": repo_uuid
            })

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e


class ChatMessageDBHelper:
    """ChatMessage DB 직접 생성을 위한 헬퍼 클래스"""

    @staticmethod
    def create_bot_message(
        db: Session,
        chat_room_id: str,
        content: str,
        sources: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bot 메시지 생성

        Args:
            db: 데이터베이스 세션
            chat_room_id: ChatRoom ID (UUID string)
            content: 메시지 내용
            sources: 소스 정보 (JSON string)

        Returns:
            생성된 메시지 정보 (id, created_at 포함)
        """
        try:
            message_id = uuid.uuid4()
            room_uuid = uuid.UUID(chat_room_id)
            now = datetime.now()

            # ChatMessage 생성
            query = text("""
                INSERT INTO chat_messages (id, chat_room_id, sender_id, sender_type, content, sources, created_at)
                VALUES (:id, :chat_room_id, NULL, 'bot', :content, :sources, :created_at)
            """)
            db.execute(query, {
                "id": message_id,
                "chat_room_id": room_uuid,
                "content": content,
                "sources": sources,
                "created_at": now
            })

            # ChatRoom의 last_message와 message_count 업데이트
            update_query = text("""
                UPDATE chat_rooms
                SET last_message = :last_message,
                    message_count = message_count + 1,
                    updated_at = :updated_at
                WHERE id = :room_id
            """)
            db.execute(update_query, {
                "last_message": content,
                "updated_at": now,
                "room_id": room_uuid
            })

            db.commit()

            return {
                "id": str(message_id),
                "chat_room_id": chat_room_id,
                "sender_type": "bot",
                "content": content,
                "sources": sources,
                "created_at": now
            }

        except Exception as e:
            db.rollback()
            raise e
