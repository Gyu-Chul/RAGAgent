import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

class APIService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("GATEWAY_URL", "http://localhost:8080")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def _parse_datetime(self, dt_str: str) -> datetime:
        """ISO 문자열을 datetime 객체로 변환"""
        try:
            # ISO 형식 파싱
            if 'T' in dt_str:
                # ISO 8601 형식 (2024-01-01T12:00:00 또는 2024-01-01T12:00:00.123456)
                if '.' in dt_str:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                # 단순 날짜 형식
                return datetime.fromisoformat(dt_str)
        except:
            # 파싱 실패 시 현재 시간 반환
            return datetime.now()

    def _convert_datetime_fields(self, data: Any, datetime_fields: List[str] = None) -> Any:
        """데이터의 datetime 필드들을 문자열에서 datetime 객체로 변환"""
        if datetime_fields is None:
            datetime_fields = ['created_at', 'last_sync', 'joined_at', 'timestamp']

        if isinstance(data, dict):
            for field in datetime_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = self._parse_datetime(data[field])
            return data
        elif isinstance(data, list):
            return [self._convert_datetime_fields(item, datetime_fields) for item in data]
        else:
            return data

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the gateway API"""
        url = f"{self.base_url}{endpoint}"
        print(f"DEBUG: Making {method} request to {url}")  # Debug logging
        try:
            timeout = 10  # 10 second timeout
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            print(f"DEBUG: Response status: {response.status_code}")  # Debug logging
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            print(f"DEBUG: Connection error to {url}: {e}")  # Debug logging
            raise Exception(f"Gateway server is not available at {url}. Connection error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"DEBUG: Timeout error to {url}: {e}")  # Debug logging
            raise Exception(f"Gateway server timeout at {url}")
        except requests.exceptions.HTTPError as e:
            print(f"DEBUG: HTTP error: {e}")  # Debug logging
            raise Exception(f"API request failed: {e}")
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}")  # Debug logging
            raise Exception(f"Unexpected error: {e}")

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories"""
        try:
            data = self._make_request("GET", "/repositories")
            return self._convert_datetime_fields(data)
        except Exception:
            # API가 구현되지 않은 경우 더미 데이터 반환
            return []

    def get_repository(self, repo_id: str) -> Dict[str, Any]:
        """Get a specific repository by ID"""
        data = self._make_request("GET", f"/repositories/{repo_id}")
        return self._convert_datetime_fields(data)

    def get_chat_rooms(self, repo_id: str) -> List[Dict[str, Any]]:
        """Get chat rooms for a repository"""
        try:
            data = self._make_request("GET", f"/repositories/{repo_id}/chat-rooms")
            return self._convert_datetime_fields(data)
        except Exception:
            # API가 구현되지 않은 경우 더미 데이터 반환
            return []

    def get_messages(self, chat_room_id: str) -> List[Dict[str, Any]]:
        """Get messages for a chat room"""
        messages = self._make_request("GET", f"/chat-rooms/{chat_room_id}/messages")
        return self._convert_datetime_fields(messages)

    def add_message(self, chat_room_id: str, sender: str, content: str) -> Dict[str, Any]:
        """Add a new message to a chat room"""
        data = {
            "chat_room_id": chat_room_id,
            "sender": sender,
            "content": content
        }
        response = self._make_request("POST", f"/chat-rooms/{chat_room_id}/messages", data)
        return self._convert_datetime_fields(response)

    def create_chat_room(self, name: str, repo_id: str) -> Dict[str, Any]:
        """Create a new chat room"""
        data = {
            "name": name,
            "repository_id": repo_id
        }
        room = self._make_request("POST", f"/repositories/{repo_id}/chat-rooms", data)
        return self._convert_datetime_fields(room)

    def get_vectordb_collections(self, repo_id: str) -> List[Dict[str, Any]]:
        """Get vector database collections for a repository"""
        return self._make_request("GET", f"/repositories/{repo_id}/vectordb/collections")

    def get_repository_members(self, repo_id: str) -> List[Dict[str, Any]]:
        """Get members of a repository"""
        members = self._make_request("GET", f"/repositories/{repo_id}/members")
        return self._convert_datetime_fields(members)

    def get_user_active_chats_count(self, user_email: str) -> int:
        """Get the count of active chat rooms for a user"""
        try:
            response = self._make_request("GET", f"/users/{user_email}/active-chats-count")
            return response.get("count", 0)
        except Exception:
            # API가 구현되지 않은 경우 더미 데이터 반환
            return 0

    def get_user_recent_activity(self, user_email: str) -> List[Dict[str, Any]]:
        """Get recent activity for a user"""
        try:
            response = self._make_request("GET", f"/users/{user_email}/recent-activity")
            return response.get("activities", [])
        except Exception:
            # API가 구현되지 않은 경우 더미 데이터 반환
            return []

# Global instance
api_service = APIService()