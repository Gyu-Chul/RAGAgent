"""
Celery 애플리케이션 설정
"""

import logging
import os
from pathlib import Path
from celery import Celery
from decouple import Config, RepositoryEnv

# .env.local 파일이 있으면 우선 사용 (로컬 개발용)
env_local_path = Path(__file__).parent.parent / '.env.local'
if env_local_path.exists():
    config = Config(RepositoryEnv(str(env_local_path)))
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
else:
    # .env.local이 없으면 환경변수 또는 기본값 사용
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# RAG Worker 로깅 설정
def setup_logging() -> None:
    """RAG Worker 프로세스 자체 로그 캡처를 위한 설정"""
    from datetime import datetime

    # 현재 날짜로 디렉토리 생성
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs") / today
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로그 파일 경로
    log_file = log_dir / f"rag_worker_{datetime.now().strftime('%H-%M-%S')}.log"

    # Celery 자체 로그를 파일로 리다이렉트
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 기본 포맷 (프로세스 자체 로그 유지)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # 루트 로거에 파일 핸들러 추가 (모든 로그를 파일로)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Celery 로거에 파일 핸들러 추가
    celery_logger = logging.getLogger("celery")
    celery_logger.addHandler(file_handler)

    # 워커 태스크 로거 설정
    task_logger = logging.getLogger("celery.task")
    task_logger.addHandler(file_handler)

    # billiard 로거 (Celery 프로세스 풀)
    billiard_logger = logging.getLogger("billiard")
    billiard_logger.addHandler(file_handler)

# 로깅 초기화
setup_logging()

# Celery 앱 인스턴스 생성
app = Celery('rag_worker')

# Celery 설정
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # 기본 celery queue 사용 (task_routes 제거)
)

# 태스크 모듈 자동 발견
app.autodiscover_tasks(['rag_worker'])

if __name__ == '__main__':
    app.start()