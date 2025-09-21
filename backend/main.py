from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from database import get_db, init_db
from models import User, UserSession
from schemas import (
    UserCreate, UserLogin, UserResponse, LoginResponse,
    Token, APIResponse
)
from auth_service import AuthService, get_current_active_user
from config import CORS_ORIGINS, ACCESS_TOKEN_EXPIRE_MINUTES

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
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# 회원가입
@app.post("/auth/signup", response_model=LoginResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """사용자 회원가입"""
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 사용자명 중복 확인
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 새 사용자 생성
    hashed_password = AuthService.get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(new_user.id), "username": new_user.username},
        expires_delta=access_token_expires
    )

    # 세션 생성
    session_expires = datetime.utcnow() + access_token_expires
    session = AuthService.create_user_session(
        db, str(new_user.id), access_token, session_expires
    )

    # 응답 생성
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    user_response = UserResponse.from_orm(new_user)

    return LoginResponse(
        success=True,
        user=user_response,
        token=token,
        message="User created successfully"
    )

# 로그인
@app.post("/auth/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    user = AuthService.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    # 세션 생성
    session_expires = datetime.utcnow() + access_token_expires
    session = AuthService.create_user_session(
        db, str(user.id), access_token, session_expires
    )

    # 응답 생성
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    user_response = UserResponse.from_orm(user)

    return LoginResponse(
        success=True,
        user=user_response,
        token=token,
        message="Login successful"
    )

# 로그아웃
@app.post("/auth/logout", response_model=APIResponse)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """사용자 로그아웃"""
    # 현재 활성 세션들 무효화
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return APIResponse(
        success=True,
        message="Logout successful"
    )

# 현재 사용자 정보 조회
@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """현재 인증된 사용자 정보 조회"""
    return UserResponse.from_orm(current_user)

# 토큰 검증
@app.post("/auth/verify-token", response_model=APIResponse)
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """토큰 유효성 검증"""
    return APIResponse(
        success=True,
        message="Token is valid",
        data={"user_id": str(current_user.id), "username": current_user.username}
    )

# 세션 정리 (관리자용)
@app.post("/auth/cleanup-sessions", response_model=APIResponse)
async def cleanup_expired_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """만료된 세션 정리"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    AuthService.cleanup_expired_sessions(db)

    return APIResponse(
        success=True,
        message="Expired sessions cleaned up"
    )

if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True
    )