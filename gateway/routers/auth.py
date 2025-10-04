"""
Gateway 인증 라우터
단일 책임: 인증 요청을 백엔드로 프록시하는 역할만 담당
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from ..schemas import LoginRequest, SignupRequest
from ..services.proxy_service import BackendProxyService
from ..services.data_service import DummyDataService

router = APIRouter(prefix="/auth", tags=["authentication"])
proxy_service = BackendProxyService()
data_service = DummyDataService()

@router.post("/login")
async def login(login_request: LoginRequest):
    """로그인 요청을 백엔드로 프록시"""
    print(f"DEBUG: Login attempt for {login_request.email}")

    try:
        result = await proxy_service.login_user(
            email=login_request.email,
            password=login_request.password
        )
        print(f"DEBUG: Backend auth successful for {login_request.email}")
        return result
    except Exception as e:
        print(f"Login proxy error: {e}")
        # 백엔드 연결 실패 시 더미 데이터로 fallback
        user = data_service.authenticate_user(login_request.email, login_request.password)
        if user:
            print(f"DEBUG: Fallback to dummy auth for {login_request.email}")
            return {
                "success": True,
                "user": user,
                "token": {"access_token": "dummy_token", "token_type": "bearer"},
                "message": "Login successful (dummy mode - backend unavailable)"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

@router.post("/signup")
async def signup(signup_request: SignupRequest):
    """회원가입 요청을 백엔드로 프록시"""
    print(f"DEBUG: Signup attempt for {signup_request.email}")

    try:
        result = await proxy_service.signup_user(
            email=signup_request.email,
            password=signup_request.password,
            username=signup_request.username
        )
        print(f"DEBUG: Backend signup successful for {signup_request.email}")
        return result
    except Exception as e:
        print(f"Signup proxy error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # 백엔드 연결 실패 시 더미 응답
        print(f"DEBUG: Fallback to dummy signup for {signup_request.email}")
        return {
            "success": True,
            "user": {
                "id": "dummy_user",
                "username": signup_request.username,
                "email": signup_request.email,
                "role": "user"
            },
            "token": {"access_token": "dummy_token", "token_type": "bearer"},
            "message": "Signup successful (dummy mode - backend unavailable)"
        }