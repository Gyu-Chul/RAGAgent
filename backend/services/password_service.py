"""
패스워드 처리 서비스
단일 책임: 패스워드 해싱 및 검증
"""

from passlib.context import CryptContext
from typing import Protocol


class PasswordHasherInterface(Protocol):
    """패스워드 해싱 인터페이스"""

    def hash_password(self, password: str) -> str:
        """패스워드 해싱"""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        ...


class BcryptPasswordHasher:
    """Bcrypt 기반 패스워드 해싱 구현"""

    def __init__(self, rounds: int = 4) -> None:
        """
        Bcrypt 패스워드 해셔 초기화

        Args:
            rounds: 해싱 라운드 수 (개발용은 4, 운영용은 12 권장)
        """
        self._context: CryptContext = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=rounds
        )

    def hash_password(self, password: str) -> str:
        """패스워드 해싱"""
        return self._context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        return self._context.verify(plain_password, hashed_password)


class PasswordService:
    """패스워드 서비스 - 패스워드 관련 비즈니스 로직"""

    def __init__(self, hasher: PasswordHasherInterface) -> None:
        self._hasher: PasswordHasherInterface = hasher

    def create_password_hash(self, password: str) -> str:
        """새 패스워드 해시 생성"""
        if not password:
            raise ValueError("패스워드는 비어있을 수 없습니다")

        if len(password) < 6:
            raise ValueError("패스워드는 최소 6자 이상이어야 합니다")

        return self._hasher.hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        if not plain_password or not hashed_password:
            return False

        return self._hasher.verify_password(plain_password, hashed_password)


# 기본 인스턴스 (의존성 주입용)
default_password_service = PasswordService(BcryptPasswordHasher())