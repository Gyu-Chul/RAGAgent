import httpx
from typing import Dict, Any
from config import BACKEND_URL

class BackendProxyService:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.timeout = 3.0

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """백엔드 로그인 요청을 프록시"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.backend_url}/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            return response.json()

    async def signup_user(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """백엔드 회원가입 요청을 프록시"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.backend_url}/auth/signup",
                json={"email": email, "password": password, "username": username},
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            return response.json()