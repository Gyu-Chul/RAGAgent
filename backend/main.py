from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .core.database import init_db
from .routers import auth

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

# 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    init_db()
    print("Backend server started successfully!")

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