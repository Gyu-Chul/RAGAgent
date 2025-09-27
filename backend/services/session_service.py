"""
세션 서비스
단일 책임: 사용자 세션 관리
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from models import UserSession


class SessionService:
    """사용자 세션 서비스"""

    def create_session(self, db: Session, user_id: str, token: str) -> UserSession:
        """새 세션 생성"""
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )

        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session_by_token(self, db: Session, token: str) -> Optional[UserSession]:
        """토큰으로 세션 조회"""
        return db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()

    def get_active_sessions_by_user(self, db: Session, user_id: str) -> list[UserSession]:
        """사용자의 활성 세션 목록 조회"""
        return db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).all()

    def invalidate_session(self, db: Session, token: str) -> bool:
        """세션 무효화"""
        try:
            session = db.query(UserSession).filter(UserSession.token == token).first()
            if session:
                session.is_active = False
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False

    def invalidate_all_user_sessions(self, db: Session, user_id: str) -> bool:
        """사용자의 모든 세션 무효화"""
        try:
            db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def cleanup_expired_sessions(self, db: Session) -> int:
        """만료된 세션 정리"""
        try:
            expired_count = db.query(UserSession).filter(
                UserSession.expires_at <= datetime.utcnow(),
                UserSession.is_active == True
            ).update({"is_active": False})
            db.commit()
            return expired_count
        except Exception:
            db.rollback()
            return 0