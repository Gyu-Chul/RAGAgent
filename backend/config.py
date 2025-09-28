import os
from urllib.parse import quote_plus
from decouple import config

# 데이터베이스 설정
# 한글 사용자명 URL 인코딩
username = quote_plus("shinminchul")
password = quote_plus("")

DATABASE_URL = config(
    "DATABASE_URL",
    default=f"postgresql://{username}:{password}@localhost:5432/postgres?client_encoding=utf8"
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
PORT = 9000