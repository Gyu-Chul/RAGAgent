"""
인증 관련 라우터
단일 책임: HTTP 요청/응답 처리 및 서비스 호출만 담당
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models import User
from schemas import (
    UserCreate, UserLogin, UserResponse, LoginResponse,
    Token, APIResponse
)
from services.auth_service import (
    auth_service,
    get_current_active_user
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=LoginResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)) -> LoginResponse:
    """사용자 회원가입"""
    try:
        # 사용자 등록
        user = auth_service.register_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already exists"
            )

        # 자동 로그인
        login_result = auth_service.login_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )

        if not login_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration successful but auto-login failed"
            )

        user, access_token = login_result

        # 응답 구성
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
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)) -> LoginResponse:
    """사용자 로그인"""
    try:
        # 사용자 로그인
        login_result = auth_service.login_user(
            db=db,
            email=user_credentials.email,
            password=user_credentials.password
        )

        if not login_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        user, access_token = login_result

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )

        # 응답 구성
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
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """사용자 로그아웃"""
    try:
        # 현재 사용자의 모든 세션 무효화
        success = auth_service._session_service.invalidate_all_user_sessions(
            db=db,
            user_id=str(current_user.id)
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout"
            )

        return APIResponse(
            success=True,
            message="Logged out successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """현재 로그인한 사용자 정보 조회"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/health")
async def auth_health_check() -> Dict[str, str]:
    """인증 서비스 헬스 체크"""
    return {
        "status": "healthy",
        "service": "authentication"
    }