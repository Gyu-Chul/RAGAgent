import os
from pathlib import Path
from urllib.parse import quote_plus
from decouple import Config, RepositoryEnv

# .env.local 파일이 있으면 우선 사용 (로컬 개발용)
env_local_path = Path(__file__).parent.parent / '.env.local'
if env_local_path.exists():
    config = Config(RepositoryEnv(str(env_local_path)))
else:
    # .env.local이 없으면 기본 .env 사용
    from decouple import config

# 데이터베이스 설정
DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql://postgres:postgres@localhost:5432/ragit"
)

# Redis 설정 (Celery broker)
REDIS_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0"
)

# JWT 설정
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS 설정
CORS_ORIGINS = [
    "http://localhost:8000",  # Frontend
    "http://localhost:8080",  # Gateway
]

# 서버 설정
HOST = "0.0.0.0"
PORT = 9090