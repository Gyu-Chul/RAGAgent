from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class AuthService:
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
        self._session_token: Optional[str] = None
        self._users_db = {
            "admin@ragagent.com": {
                "id": "1",
                "username": "admin",
                "email": "admin@ragagent.com",
                "password": "admin123",
                "role": "admin",
                "name": "Administrator",
                "created_at": datetime.now()
            },
            "user@ragagent.com": {
                "id": "2",
                "username": "user",
                "email": "user@ragagent.com",
                "password": "user123",
                "role": "user",
                "name": "Regular User",
                "created_at": datetime.now()
            }
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        if email in self._users_db:
            user = self._users_db[email]
            if user["password"] == password:
                self._current_user = user.copy()
                self._current_user.pop("password")
                self._session_token = f"token_{user['id']}_{datetime.now().timestamp()}"
                return {
                    "success": True,
                    "user": self._current_user,
                    "token": self._session_token
                }

        return {"success": False, "message": "Invalid credentials"}

    def signup(self, username: str, email: str, password: str, name: str) -> Dict[str, Any]:
        if email in self._users_db:
            return {"success": False, "message": "Email already exists"}

        user_id = str(len(self._users_db) + 1)
        new_user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password": password,
            "role": "user",
            "name": name,
            "created_at": datetime.now()
        }

        self._users_db[email] = new_user
        self._current_user = new_user.copy()
        self._current_user.pop("password")
        self._session_token = f"token_{user_id}_{datetime.now().timestamp()}"

        return {
            "success": True,
            "user": self._current_user,
            "token": self._session_token
        }

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

        email = self._current_user["email"]
        self._users_db[email]["name"] = name
        self._current_user["name"] = name

        if password:
            self._users_db[email]["password"] = password

        return {"success": True, "message": "Profile updated successfully"}