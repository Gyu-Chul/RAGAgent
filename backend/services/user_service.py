"""
사용자 서비스
단일 책임: 사용자 CRUD 및 사용자 관련 비즈니스 로직
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime

from models import User, UserSession
from services.password_service import PasswordService
from core.database import get_db


class UserService:
    """사용자 서비스"""

    def __init__(self, password_service: PasswordService) -> None:
        self._password_service: PasswordService = password_service

    def create_user(self, db: Session, username: str, email: str, password: str) -> Optional[User]:
        """새 사용자 생성"""
        try:
            # 패스워드 해싱
            hashed_password = self._password_service.create_password_hash(password)

            # 사용자 생성
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True
            )

            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        except IntegrityError:
            db.rollback()
            return None
        except Exception:
            db.rollback()
            return None

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        return db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None

        if not self._password_service.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    def update_last_login(self, db: Session, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트 (현재 미구현)"""
        # last_login 필드가 데이터베이스에 없으므로 임시로 True 반환
        return True

    def deactivate_user(self, db: Session, user_id: str) -> bool:
        """사용자 비활성화"""
        try:
            user = self.get_user_by_id(db, user_id)
            if user:
                user.is_active = False
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False