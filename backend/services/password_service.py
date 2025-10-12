"""
패스워드 처리 서비스
단일 책임: 패스워드 해싱 및 검증
"""

import bcrypt
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
    """Bcrypt 기반 패스워드 해싱 구현 (bcrypt 라이브러리 직접 사용)"""

    def __init__(self, rounds: int = 4) -> None:
        """
        Bcrypt 패스워드 해셔 초기화

        Args:
            rounds: 해싱 라운드 수 (개발용은 4, 운영용은 12 권장)
        """
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """패스워드 해싱"""
        # 문자열을 바이트로 변환 (72바이트로 제한)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        # 문자열을 바이트로 변환 (72바이트로 제한)
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)


class PasswordService:
    """패스워드 서비스 - 패스워드 관련 비즈니스 로직"""

    def __init__(self, hasher: PasswordHasherInterface) -> None:
        self._hasher: PasswordHasherInterface = hasher

    def create_password_hash(self, password: str) -> str:
        """새 패스워드 해시 생성"""
        # 패스워드 길이 제한 제거 - 공백도 허용
        # bcrypt는 72바이트 제한이 있으므로 미리 잘라냄
        password_bytes = password.encode('utf-8')
        print(f"DEBUG: Password byte length = {len(password_bytes)}")
        if len(password_bytes) > 72:
            print(f"DEBUG: Truncating password from {len(password_bytes)} to 72 bytes")
            password = password_bytes[:72].decode('utf-8', errors='ignore')

        return self._hasher.hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        if not plain_password or not hashed_password:
            return False

        # bcrypt는 72바이트 제한이 있으므로 미리 잘라냄
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')

        return self._hasher.verify_password(plain_password, hashed_password)


# 기본 인스턴스 (의존성 주입용)
default_password_service = PasswordService(BcryptPasswordHasher())