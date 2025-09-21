from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests

class AuthService:
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
        self._session_token: Optional[str] = None
        self.gateway_url = "http://localhost:8080"

    def login(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = requests.post(f"{self.gateway_url}/auth/login", json={
                "email": email,
                "password": password
            }, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self._current_user = data["user"]
                    self._session_token = data["token"]["access_token"]
                    return {
                        "success": True,
                        "user": self._current_user,
                        "token": self._session_token
                    }
                else:
                    return {"success": False, "message": data.get("message", "Login failed")}
            else:
                try:
                    error_data = response.json()
                    return {"success": False, "message": error_data.get("detail", "Invalid credentials")}
                except:
                    return {"success": False, "message": "Invalid credentials"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Gateway server not available"}

    def signup(self, username: str, email: str, password: str, name: str) -> Dict[str, Any]:
        try:
            response = requests.post(f"{self.gateway_url}/auth/signup", json={
                "email": email,
                "password": password,
                "username": username
            }, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self._current_user = data["user"]
                    self._session_token = data["token"]["access_token"]
                    return {
                        "success": True,
                        "user": self._current_user,
                        "token": self._session_token
                    }
                else:
                    return {"success": False, "message": data.get("message", "Signup failed")}
            else:
                try:
                    error_data = response.json()
                    return {"success": False, "message": error_data.get("detail", "Signup failed")}
                except:
                    return {"success": False, "message": "Signup failed"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Gateway server not available"}

    def logout(self) -> None:
        self._current_user = None
        self._session_token = None

    def is_authenticated(self) -> bool:
        return self._current_user is not None and self._session_token is not None

    def is_admin(self) -> bool:
        return self.is_authenticated() and self._current_user.get("role") == "admin"

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self._current_user

    def update_profile(self, name: str, password: str = None) -> Dict[str, Any]:
        if not self.is_authenticated():
            return {"success": False, "message": "Not authenticated"}

        # 현재는 간단히 로컬에서만 업데이트 (향후 Gateway API 추가 예정)
        self._current_user["username"] = name

        return {"success": True, "message": "Profile updated successfully"}