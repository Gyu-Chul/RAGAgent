"""
Chat API 라우터
단일 책임: Chat 관련 HTTP 요청 처리
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.chat_service import ChatRoomService, ChatMessageService
from ..services.repository_service import RepositoryService
from ..services.auth_service import get_current_active_user
from ..schemas.chat import (
    ChatRoomCreate,
    ChatRoomUpdate,
    ChatRoomResponse,
    ChatMessageCreate,
    ChatMessageResponse
)
from ..models.user import User

router = APIRouter(prefix="/api/repositories", tags=["chat"])


# ChatRoom Endpoints

@router.post("/{repo_id}/chat-rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
def create_chat_room(
    repo_id: str,
    room_data: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새로운 ChatRoom 생성"""
    # Repository 접근 권한 확인
    if not RepositoryService.check_user_permission(db, repo_id, str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this repository"
        )

    # Repository 존재 확인
    repository = RepositoryService.get_repository(db, repo_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    # ChatRoom 생성
    chat_room = ChatRoomService.create_chat_room(db, room_data, str(current_user.id))

    # 응답 생성
    room_dict = {
        "id": str(chat_room.id),
        "name": chat_room.name,
        "repository_id": str(chat_room.repository_id),
        "created_by": str(chat_room.created_by),
        "message_count": chat_room.message_count or 0,
        "last_message": chat_room.last_message,
        "created_at": chat_room.created_at,
        "updated_at": chat_room.updated_at
    }

    return room_dict


@router.get("/{repo_id}/chat-rooms", response_model=List[ChatRoomResponse])
def get_chat_rooms(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Repository의 모든 ChatRoom 조회"""
    # Repository 접근 권한 확인
    if not RepositoryService.check_user_permission(db, repo_id, str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this repository"
        )

    # ChatRoom 목록 조회
    chat_rooms = ChatRoomService.get_repository_chat_rooms(db, repo_id)

    # 응답 생성
    result = []
    for room in chat_rooms:
        room_dict = {
            "id": str(room.id),
            "name": room.name,
            "repository_id": str(room.repository_id),
            "created_by": str(room.created_by),
            "message_count": room.message_count or 0,
            "last_message": room.last_message,
            "created_at": room.created_at,
            "updated_at": room.updated_at
        }
        result.append(room_dict)

    return result


@router.get("/chat-rooms/{room_id}", response_model=ChatRoomResponse)
def get_chat_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 ChatRoom 조회"""
    chat_room = ChatRoomService.get_chat_room(db, room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Repository 접근 권한 확인
    if not RepositoryService.check_user_permission(
        db, str(chat_room.repository_id), str(current_user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this chat room"
        )

    # 응답 생성
    room_dict = {
        "id": str(chat_room.id),
        "name": chat_room.name,
        "repository_id": str(chat_room.repository_id),
        "created_by": str(chat_room.created_by),
        "message_count": chat_room.message_count or 0,
        "last_message": chat_room.last_message,
        "created_at": chat_room.created_at,
        "updated_at": chat_room.updated_at
    }

    return room_dict


@router.put("/chat-rooms/{room_id}", response_model=ChatRoomResponse)
def update_chat_room(
    room_id: str,
    room_data: ChatRoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ChatRoom 업데이트"""
    chat_room = ChatRoomService.get_chat_room(db, room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # 생성자만 수정 가능
    if str(chat_room.created_by) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can update this chat room"
        )

    updated_room = ChatRoomService.update_chat_room(db, room_id, room_data)

    # 응답 생성
    room_dict = {
        "id": str(updated_room.id),
        "name": updated_room.name,
        "repository_id": str(updated_room.repository_id),
        "created_by": str(updated_room.created_by),
        "message_count": updated_room.message_count or 0,
        "last_message": updated_room.last_message,
        "created_at": updated_room.created_at,
        "updated_at": updated_room.updated_at
    }

    return room_dict


@router.delete("/chat-rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ChatRoom 삭제"""
    chat_room = ChatRoomService.get_chat_room(db, room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # 생성자만 삭제 가능
    if str(chat_room.created_by) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can delete this chat room"
        )

    success = ChatRoomService.delete_chat_room(db, room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete chat room"
        )


# ChatMessage Endpoints

@router.post("/chat-rooms/{room_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    room_id: str,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새로운 ChatMessage 생성"""
    # ChatRoom 존재 확인
    chat_room = ChatRoomService.get_chat_room(db, room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Repository 접근 권한 확인
    if not RepositoryService.check_user_permission(
        db, str(chat_room.repository_id), str(current_user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to send messages in this chat room"
        )

    # 메시지 생성
    user_id = str(current_user.id) if message_data.sender_type == "user" else None
    message = ChatMessageService.create_message(db, message_data, user_id)

    # 사용자 메시지인 경우 RAG Worker에 쿼리 전송
    if message_data.sender_type == "user":
        import logging
        logger = logging.getLogger(__name__)

        try:
            from ..core.celery import celery_app

            logger.info(f"🤖 Triggering RAG chat query for message: {message.id}")

            # Celery task 트리거
            task = celery_app.send_task(
                'rag_worker.tasks.chat_query',
                kwargs={
                    'chat_room_id': str(chat_room.id),
                    'repo_id': str(chat_room.repository_id),
                    'user_message': message.content,
                    'top_k': 5
                }
            )

            logger.info(f"✅ RAG task sent. Task ID: {task.id}")

        except Exception as task_error:
            logger.error(f"❌ Failed to trigger RAG task: {str(task_error)}", exc_info=True)
            # Task 실패해도 메시지는 저장되었으므로 계속 진행

    # 응답 생성
    message_dict = {
        "id": str(message.id),
        "chat_room_id": str(message.chat_room_id),
        "sender_id": str(message.sender_id) if message.sender_id else None,
        "sender_type": message.sender_type,
        "content": message.content,
        "sources": message.sources,
        "created_at": message.created_at
    }

    return message_dict


@router.get("/chat-rooms/{room_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ChatRoom의 모든 메시지 조회"""
    # ChatRoom 존재 확인
    chat_room = ChatRoomService.get_chat_room(db, room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Repository 접근 권한 확인
    if not RepositoryService.check_user_permission(
        db, str(chat_room.repository_id), str(current_user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view messages in this chat room"
        )

    # 메시지 목록 조회
    messages = ChatMessageService.get_chat_room_messages(db, room_id)

    # 응답 생성
    result = []
    for msg in messages:
        message_dict = {
            "id": str(msg.id),
            "chat_room_id": str(msg.chat_room_id),
            "sender_id": str(msg.sender_id) if msg.sender_id else None,
            "sender_type": msg.sender_type,
            "content": msg.content,
            "sources": msg.sources,
            "created_at": msg.created_at
        }
        result.append(message_dict)

    return result


@router.delete("/chat-rooms/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ChatMessage 삭제"""
    message = ChatMessageService.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # 발신자만 삭제 가능
    if message.sender_id and str(message.sender_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the sender can delete this message"
        )

    success = ChatMessageService.delete_message(db, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete message"
        )
