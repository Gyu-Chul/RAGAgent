"""
RAGIT SDK - RAG with Gateway-Backend Architecture Software Development Kit

통합 프로세스 관리, Docker 배포, 환경 설정을 위한 SDK 패키지

구조:
- core/: 핵심 프로세스 및 도커 관리
- tests/: 테스트 및 검증 스크립트
"""

__version__ = "0.1.0"
__author__ = "GyuChul Team"

from .cli import main
from .config import RagitConfig
from .core import ProcessManager, DockerManager

__all__ = [
    "main",
    "RagitConfig",
    "ProcessManager",
    "DockerManager"
]