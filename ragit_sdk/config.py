"""
RAGIT 설정 관리
환경변수, 포트, 경로 등 설정 정보 관리
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RagitConfig:
    """RAGIT 설정 클래스"""

    def __init__(self) -> None:
        # 기본 경로 설정
        self.work_dir: Path = Path.cwd()
        self.log_dir: Path = self.work_dir / "logs"
        self.data_dir: Path = self.work_dir / "data"

        # 환경 설정
        self.environment: str = os.getenv("RAGIT_ENV", "development")

        # 서비스 포트 설정
        self.frontend_port: int = int(os.getenv("FRONTEND_PORT", "8000"))
        self.backend_port: int = int(os.getenv("BACKEND_PORT", "8001"))
        self.gateway_port: int = int(os.getenv("GATEWAY_PORT", "8080"))

        # 데이터베이스 설정
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/ragit"
        )

        # Redis 설정
        self.redis_url: str = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        # JWT 설정
        self.secret_key: str = os.getenv(
            "SECRET_KEY",
            "your-secret-key-here"
        )
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )

        # 로깅 설정
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # 서비스 실행 명령어
        self.service_commands: Dict[str, Dict[str, Any]] = {
            "backend": {
                "cmd": ["python", "-m", "uvicorn", "backend.main:app",
                       "--host", "0.0.0.0", "--port", str(self.backend_port)],
                "cwd": self.work_dir,
                "env": self._get_backend_env()
            },
            "frontend": {
                "cmd": ["python", "-m", "frontend.main"],
                "cwd": self.work_dir,
                "env": self._get_frontend_env()
            },
            "gateway": {
                "cmd": ["python", "-m", "gateway.main"],
                "cwd": self.work_dir,
                "env": self._get_gateway_env()
            },
            "rag_worker": {
                "cmd": ["python", "-m", "celery", "worker", "-A", "rag_worker.celery_app",
                       "--loglevel=info", "--pool=solo"] if os.name == 'nt'
                       else ["python", "-m", "celery", "worker", "-A", "rag_worker.celery_app",
                            "--loglevel=info"],
                "cwd": self.work_dir,
                "env": self._get_rag_worker_env()
            }
        }

        # 디렉토리 생성
        self._create_directories()

    def _get_base_env(self) -> Dict[str, str]:
        """공통 환경변수 반환"""
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": self.database_url,
            "REDIS_URL": self.redis_url,
            "SECRET_KEY": self.secret_key,
            "ALGORITHM": self.algorithm,
            "ACCESS_TOKEN_EXPIRE_MINUTES": str(self.access_token_expire_minutes),
            "PYTHONPATH": str(self.work_dir)
        })
        return env

    def _get_backend_env(self) -> Dict[str, str]:
        """Backend 서비스 환경변수"""
        env = self._get_base_env()
        env.update({
            "SERVICE_NAME": "backend",
            "PORT": str(self.backend_port)
        })
        return env

    def _get_frontend_env(self) -> Dict[str, str]:
        """Frontend 서비스 환경변수"""
        env = self._get_base_env()
        env.update({
            "SERVICE_NAME": "frontend",
            "PORT": str(self.frontend_port),
            "GATEWAY_URL": f"http://localhost:{self.gateway_port}",
            "BACKEND_URL": f"http://localhost:{self.backend_port}"
        })
        return env

    def _get_gateway_env(self) -> Dict[str, str]:
        """Gateway 서비스 환경변수"""
        env = self._get_base_env()
        env.update({
            "SERVICE_NAME": "gateway",
            "PORT": str(self.gateway_port),
            "BACKEND_URL": f"http://localhost:{self.backend_port}"
        })
        return env

    def _get_rag_worker_env(self) -> Dict[str, str]:
        """RAG Worker 서비스 환경변수"""
        env = self._get_base_env()
        env.update({
            "SERVICE_NAME": "rag_worker",
            "BACKEND_URL": f"http://localhost:{self.backend_port}"
        })
        return env

    def _create_directories(self) -> None:
        """필요한 디렉토리 생성"""
        self.log_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """특정 서비스 설정 반환"""
        return self.service_commands.get(service_name)

    def get_all_services(self) -> list[str]:
        """모든 서비스 이름 반환"""
        return list(self.service_commands.keys())

    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() in ['production', 'prod']

    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment.lower() in ['development', 'dev']

    def get_docker_compose_file(self, mode: str = "dev") -> str:
        """Docker Compose 파일 경로 반환"""
        if mode == "prod":
            return "docker-compose.prod.yml"
        return "docker-compose.yml"

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "work_dir": str(self.work_dir),
            "log_dir": str(self.log_dir),
            "data_dir": str(self.data_dir),
            "environment": self.environment,
            "frontend_port": self.frontend_port,
            "backend_port": self.backend_port,
            "gateway_port": self.gateway_port,
            "database_url": self.database_url,
            "redis_url": self.redis_url,
            "log_level": self.log_level
        }