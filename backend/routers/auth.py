from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models import User, UserSession
from app.schemas import (
    UserCreate, UserLogin, UserResponse, LoginResponse,
    Token, APIResponse
)
from app.services.auth_service import AuthService, get_current_active_user
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=LoginResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """사용자 회원가입"""
    try:
        # 기존 사용자 확인
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
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
        AuthService.create_user_session(
            db=db,
            user_id=str(new_user.id),
            session_token=access_token,
            expires_at=session_expires
        )

        # 응답 데이터 구성
        user_response = UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at
        )

        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return LoginResponse(
            success=True,
            user=user_response,
            token=token_response,
            message="User created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    try:
        # 사용자 인증
        user = AuthService.authenticate_user(
            db=db,
            email=user_credentials.email,
            password=user_credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )

        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )

        # 세션 생성
        session_expires = datetime.utcnow() + access_token_expires
        AuthService.create_user_session(
            db=db,
            user_id=str(user.id),
            session_token=access_token,
            expires_at=session_expires
        )

        # 응답 데이터 구성
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )

        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return LoginResponse(
            success=True,
            user=user_response,
            token=token_response,
            message="Login successful"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout", response_model=APIResponse)
async def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """사용자 로그아웃"""
    try:
        # 현재 활성 세션들을 모두 비활성화
        db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).update({"is_active": False})

        db.commit()

        return APIResponse(
            success=True,
            message="Logged out successfully"
        )

    except Exception as e:
        print(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """현재 로그인한 사용자 정보 조회"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )