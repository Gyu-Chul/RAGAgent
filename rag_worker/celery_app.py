"""
Celery 애플리케이션 설정
"""

from celery import Celery
import os

# Celery 앱 인스턴스 생성
app = Celery('rag_worker')

# Celery 설정
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'rag_worker.tasks.*': {'queue': 'rag_tasks'},
    }
)

# 태스크 모듈 자동 발견
app.autodiscover_tasks(['rag_worker'])

if __name__ == '__main__':
    app.start()