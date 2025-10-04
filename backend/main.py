import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .core.database import init_db
from .routers import auth
from .routers import repository

# 로그 설정
def setup_logging() -> None:
    """백엔드 프로세스 자체 로그 캡처를 위한 설정"""
    from datetime import datetime

    # 현재 날짜로 디렉토리 생성
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs") / today
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로그 파일 경로
    log_file = log_dir / f"backend_{datetime.now().strftime('%H-%M-%S')}.log"

    # uvicorn과 FastAPI 자체 로그를 파일로 리다이렉트
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 기본 포맷 (프로세스 자체 로그 유지)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # 루트 로거에 파일 핸들러 추가 (모든 로그를 파일로)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # uvicorn 로거에 파일 핸들러 추가
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.addHandler(file_handler)

    # FastAPI 접근 로그 활성화
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addHandler(file_handler)

# 로깅 초기화
setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title="RAG Agent Backend",
    description="Backend API for RAG Agent with PostgreSQL and JWT authentication",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(repository.router)

# 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    init_db()

# 기본 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "RAG Agent Backend API",
        "version": "1.0.0",
        "status": "running"
    }

# 헬스 체크
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Backend server is running"
    }