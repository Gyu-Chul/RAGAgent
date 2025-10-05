"""
Celery Client for Backend Service
Backend에서 task를 send하기 위한 Celery 클라이언트
"""

import os
from celery import Celery

# Redis URL 환경변수에서 가져오기
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 클라이언트 생성 (task 정의 없이 send만 사용)
celery_app = Celery(
    "backend",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
    task_soft_time_limit=25 * 60,  # 25분
)
