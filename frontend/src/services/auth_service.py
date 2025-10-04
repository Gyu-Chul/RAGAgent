from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
import os

class AuthService:
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
        self._session_token: Optional[str] = None
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080")

    def login(self, email: str, password: str) -> Dict[str, Any]:
        try:
            url = f"{self.gateway_url}/auth/login"
            print(f"DEBUG: Login request to {url}")  # Debug logging
            print(f"DEBUG: Email={email}, Password={'*' * len(password)}")

            response = requests.post(url, json={
                "email": email,
                "password": password
            }, timeout=10)

            print(f"DEBUG: Response status={response.status_code}")
            print(f"DEBUG: Response body={response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self._current_user = data["user"]
                    self._session_token = data["token"]["access_token"]
                    print(f"DEBUG: Login successful for {email}")
                    return {
                        "success": True,
                        "user": self._current_user,
                        "token": self._session_token
                    }
                else:
                    print(f"DEBUG: Login failed - {data.get('message', 'Unknown error')}")
                    return {"success": False, "message": data.get("message", "Login failed")}
            else:
                try:
                    error_data = response.json()
                    print(f"DEBUG: Login error - {error_data.get('detail', 'Unknown error')}")
                    return {"success": False, "message": error_data.get("detail", "Invalid credentials")}
                except:
                    print(f"DEBUG: Login error - Invalid credentials")
                    return {"success": False, "message": "Invalid credentials"}
        except requests.exceptions.ConnectionError as e:
            print(f"DEBUG: Connection error - {e}")
            return {"success": False, "message": "Gateway server not available"}
        except Exception as e:
            print(f"DEBUG: Unexpected error - {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def signup(self, username: str, email: str, password: str, name: str) -> Dict[str, Any]:
        try:
            url = f"{self.gateway_url}/auth/signup"
            print(f"DEBUG: Signup request to {url}")
            print(f"DEBUG: Username={username}, Email={email}, Password={'*' * len(password)}")

            response = requests.post(url, json={
                "email": email,
                "password": password,
                "username": username
            }, timeout=10)

            print(f"DEBUG: Response status={response.status_code}")
            print(f"DEBUG: Response body={response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self._current_user = data["user"]
                    self._session_token = data["token"]["access_token"]
                    print(f"DEBUG: Signup successful for {email}")
                    return {
                        "success": True,
                        "user": self._current_user,
                        "token": self._session_token
                    }
                else:
                    print(f"DEBUG: Signup failed - {data.get('message', 'Unknown error')}")
                    return {"success": False, "message": data.get("message", "Signup failed")}
            else:
                try:
                    error_data = response.json()
                    print(f"DEBUG: Signup error - {error_data.get('detail', 'Unknown error')}")
                    return {"success": False, "message": error_data.get("detail", "Signup failed")}
                except:
                    print(f"DEBUG: Signup error - Invalid response")
                    return {"success": False, "message": "Signup failed"}
        except requests.exceptions.ConnectionError as e:
            print(f"DEBUG: Connection error - {e}")
            return {"success": False, "message": "Gateway server not available"}
        except Exception as e:
            print(f"DEBUG: Unexpected error - {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

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