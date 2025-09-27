"""
인증 서비스 - 리팩토링된 버전
단일 책임: 사용자 인증 및 권한 관리 오케스트레이션
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models import User
from schemas import TokenData
from core.database import get_db
from services.password_service import default_password_service
from services.token_service import default_token_service
from services.user_service import UserService
from services.session_service import SessionService


# HTTP Bearer 스키마
security = HTTPBearer()


class AuthenticationService:
    """인증 서비스 - 인증 관련 오케스트레이션"""

    def __init__(
        self,
        user_service: UserService,
        session_service: SessionService
    ) -> None:
        self._user_service: UserService = user_service
        self._session_service: SessionService = session_service

    def register_user(self, db: Session, username: str, email: str, password: str) -> Optional[User]:
        """사용자 회원가입"""
        # 중복 체크
        if self._user_service.get_user_by_email(db, email):
            return None

        if self._user_service.get_user_by_username(db, username):
            return None

        return self._user_service.create_user(db, username, email, password)

    def login_user(self, db: Session, email: str, password: str) -> Optional[tuple[User, str]]:
        """사용자 로그인"""
        user = self._user_service.authenticate_user(db, email, password)
        if not user:
            return None

        # 액세스 토큰 생성
        access_token = default_token_service.create_access_token(str(user.id), user.username)

        # 세션 생성
        self._session_service.create_session(db, str(user.id), access_token)

        # 마지막 로그인 시간 업데이트
        self._user_service.update_last_login(db, str(user.id))

        return user, access_token

    def logout_user(self, db: Session, token: str) -> bool:
        """사용자 로그아웃"""
        return self._session_service.invalidate_session(db, token)

    def get_current_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """토큰으로부터 현재 사용자 조회"""
        # 토큰 검증
        token_data = default_token_service.verify_access_token(token)
        if not token_data:
            return None

        # 세션 확인
        session = self._session_service.get_session_by_token(db, token)
        if not session:
            return None

        # 사용자 조회
        return self._user_service.get_user_by_id(db, token_data.user_id)


class AuthorizationService:
    """권한 서비스 - 권한 확인 관련"""

    def __init__(self, user_service: UserService) -> None:
        self._user_service: UserService = user_service

    def is_admin(self, user: User) -> bool:
        """관리자 권한 확인"""
        return user.username == "admin"  # 임시 구현

    def can_access_resource(self, user: User, resource_id: str) -> bool:
        """리소스 접근 권한 확인"""
        # 관리자는 모든 리소스 접근 가능
        if self.is_admin(user):
            return True

        # 일반 사용자 권한 로직
        return True  # 임시로 모든 접근 허용


# 서비스 인스턴스 생성 (의존성 주입용)
user_service = UserService(default_password_service)
session_service = SessionService()
auth_service = AuthenticationService(user_service, session_service)
authorization_service = AuthorizationService(user_service)


# FastAPI 의존성 함수들
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 사용자 조회 (FastAPI 의존성)"""
    token = credentials.credentials
    user = auth_service.get_current_user_from_token(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자 조회 (FastAPI 의존성)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자 사용자 조회 (FastAPI 의존성)"""
    if not authorization_service.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# 레거시 호환성을 위한 AuthService 클래스 (Deprecated)
class AuthService:
    """
    레거시 호환성을 위한 AuthService 클래스
    새 코드에서는 AuthenticationService와 AuthorizationService를 직접 사용하세요
    """

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증 (Deprecated)"""
        return default_password_service.verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """패스워드 해싱 (Deprecated)"""
        return default_password_service.create_password_hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta=None) -> str:
        """JWT 토큰 생성 (Deprecated)"""
        user_id = data.get("sub", "")
        username = data.get("username", "")
        return default_token_service.create_access_token(user_id, username)