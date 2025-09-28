"""
JWT 토큰 서비스
단일 책임: JWT 토큰 생성, 검증, 관리
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Protocol
from jose import JWTError, jwt

from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ..schemas import TokenData


class TokenProviderInterface(Protocol):
    """토큰 제공자 인터페이스"""

    def create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """토큰 생성"""
        ...

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        ...


class JWTTokenProvider:
    """JWT 토큰 제공자"""

    def __init__(self, secret_key: str, algorithm: str) -> None:
        self._secret_key: str = secret_key
        self._algorithm: str = algorithm

    def create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """JWT 토큰 생성"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except JWTError:
            return None


class TokenService:
    """토큰 서비스 - 토큰 관련 비즈니스 로직"""

    def __init__(self, provider: TokenProviderInterface) -> None:
        self._provider: TokenProviderInterface = provider

    def create_access_token(self, user_id: str, username: str) -> str:
        """사용자용 액세스 토큰 생성"""
        data = {
            "sub": user_id,
            "username": username,
            "type": "access"
        }
        return self._provider.create_token(data)

    def create_refresh_token(self, user_id: str) -> str:
        """리프레시 토큰 생성"""
        data = {
            "sub": user_id,
            "type": "refresh"
        }
        expires_delta = timedelta(days=30)  # 리프레시 토큰은 30일
        return self._provider.create_token(data, expires_delta)

    def verify_access_token(self, token: str) -> Optional[TokenData]:
        """액세스 토큰 검증 및 TokenData 반환"""
        payload = self._provider.verify_token(token)
        if not payload:
            return None

        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        username = payload.get("username")

        if not user_id:
            return None

        return TokenData(user_id=user_id, username=username)

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """리프레시 토큰 검증 및 사용자 ID 반환"""
        payload = self._provider.verify_token(token)
        if not payload:
            return None

        if payload.get("type") != "refresh":
            return None

        return payload.get("sub")


# 기본 인스턴스 (의존성 주입용)
default_token_service = TokenService(JWTTokenProvider(SECRET_KEY, ALGORITHM))