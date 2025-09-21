from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uvicorn
from datetime import datetime, timedelta
import json
import httpx
import asyncio

# Request/Response Models
class MessageRequest(BaseModel):
    chat_room_id: str
    sender: str
    content: str

class ChatRoomRequest(BaseModel):
    name: str
    repository_id: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    username: str

# Backend service configuration
BACKEND_URL = "http://localhost:9000"

class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    sender: str
    content: str
    timestamp: datetime
    sources: Optional[List[str]] = None

# Gateway App
app = FastAPI(title="RAG Agent Gateway", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy Data Service (프론트엔드에서 이전)
class DummyDataService:
    def __init__(self):
        self.repositories = [
            {
                "id": "1",
                "name": "awesome-ml-project",
                "description": "A comprehensive machine learning project with RAG capabilities",
                "owner": "AI-Corp",
                "url": "https://github.com/AI-Corp/awesome-ml-project",
                "stars": 1250,
                "language": "Python",
                "status": "active",
                "created_at": datetime.now() - timedelta(days=30),
                "last_sync": datetime.now() - timedelta(hours=2),
                "members_count": 5,
                "vectordb_status": "healthy",
                "collections_count": 3
            },
            {
                "id": "2",
                "name": "react-dashboard",
                "description": "Modern React dashboard with analytics and reporting",
                "owner": "WebDev-Team",
                "url": "https://github.com/WebDev-Team/react-dashboard",
                "stars": 890,
                "language": "JavaScript",
                "status": "active",
                "created_at": datetime.now() - timedelta(days=45),
                "last_sync": datetime.now() - timedelta(hours=6),
                "members_count": 3,
                "vectordb_status": "healthy",
                "collections_count": 2
            },
            {
                "id": "3",
                "name": "microservices-api",
                "description": "Scalable microservices architecture with Docker and Kubernetes",
                "owner": "DevOps-Masters",
                "url": "https://github.com/DevOps-Masters/microservices-api",
                "stars": 2100,
                "language": "Go",
                "status": "syncing",
                "created_at": datetime.now() - timedelta(days=60),
                "last_sync": datetime.now() - timedelta(minutes=15),
                "members_count": 8,
                "vectordb_status": "syncing",
                "collections_count": 5
            }
        ]

        self.chat_rooms = [
            {
                "id": "1",
                "name": "General Discussion",
                "repository_id": "1",
                "created_at": datetime.now() - timedelta(days=5),
                "last_message": "How do I implement the new transformer model?",
                "message_count": 45
            },
            {
                "id": "2",
                "name": "Bug Analysis",
                "repository_id": "1",
                "created_at": datetime.now() - timedelta(days=3),
                "last_message": "Found the issue in the data preprocessing pipeline",
                "message_count": 23
            },
            {
                "id": "3",
                "name": "Feature Requests",
                "repository_id": "2",
                "created_at": datetime.now() - timedelta(days=2),
                "last_message": "Can we add real-time notifications?",
                "message_count": 18
            }
        ]

        self.messages = [
            {
                "id": "1",
                "chat_room_id": "1",
                "sender": "user",
                "content": "How does the transformer architecture work in this project?",
                "timestamp": datetime.now() - timedelta(minutes=10)
            },
            {
                "id": "2",
                "chat_room_id": "1",
                "sender": "bot",
                "content": "Based on the repository code, the transformer architecture is implemented in the `models/transformer.py` file. It uses a multi-head attention mechanism with 8 attention heads and a hidden dimension of 512. The model processes input sequences through:\n\n1. Token embedding layer\n2. Positional encoding\n3. Multiple transformer blocks (6 layers)\n4. Final linear projection\n\nThe implementation follows the standard transformer architecture with residual connections and layer normalization.",
                "timestamp": datetime.now() - timedelta(minutes=9),
                "sources": [
                    "models/transformer.py",
                    "config/model_config.yaml",
                    "docs/architecture.md"
                ]
            },
            {
                "id": "3",
                "chat_room_id": "1",
                "sender": "user",
                "content": "What are the hyperparameters used for training?",
                "timestamp": datetime.now() - timedelta(minutes=5)
            },
            {
                "id": "4",
                "chat_room_id": "1",
                "sender": "bot",
                "content": "According to the training configuration files, the hyperparameters are:\n\n**Model Parameters:**\n- Learning rate: 0.0001\n- Batch size: 32\n- Sequence length: 512\n- Hidden dimension: 512\n- Number of layers: 6\n- Attention heads: 8\n\n**Training Parameters:**\n- Optimizer: AdamW\n- Weight decay: 0.01\n- Warmup steps: 4000\n- Max epochs: 100\n- Early stopping patience: 10\n\nThese are defined in `config/training_config.yaml` and `scripts/train.py`.",
                "timestamp": datetime.now() - timedelta(minutes=4),
                "sources": [
                    "config/training_config.yaml",
                    "scripts/train.py"
                ]
            }
        ]

        self.vectordb_collections = [
            {
                "id": "1",
                "name": "code_embeddings",
                "repository_id": "1",
                "description": "Embeddings for source code files",
                "entity_count": 1520,
                "dimension": 768,
                "index_type": "HNSW",
                "status": "ready"
            },
            {
                "id": "2",
                "name": "documentation_embeddings",
                "repository_id": "1",
                "description": "Embeddings for documentation and README files",
                "entity_count": 342,
                "dimension": 768,
                "index_type": "HNSW",
                "status": "ready"
            },
            {
                "id": "3",
                "name": "issue_embeddings",
                "repository_id": "1",
                "description": "Embeddings for GitHub issues and discussions",
                "entity_count": 89,
                "dimension": 768,
                "index_type": "HNSW",
                "status": "ready"
            }
        ]

        self.repository_members = [
            {
                "id": "1",
                "repository_id": "1",
                "user_id": "1",
                "username": "admin",
                "role": "admin",
                "email": "admin@ragagent.com",
                "joined_at": datetime.now() - timedelta(days=30)
            },
            {
                "id": "2",
                "repository_id": "1",
                "user_id": "2",
                "username": "user",
                "role": "member",
                "email": "user@ragagent.com",
                "joined_at": datetime.now() - timedelta(days=25)
            },
            {
                "id": "3",
                "repository_id": "1",
                "user_id": "3",
                "username": "developer1",
                "role": "member",
                "email": "dev1@company.com",
                "joined_at": datetime.now() - timedelta(days=20)
            }
        ]

        # 사용자 데이터
        self.users = [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@ragagent.com",
                "password": "admin123",
                "role": "admin",
                "created_at": datetime.now() - timedelta(days=30)
            },
            {
                "id": "2",
                "username": "user",
                "email": "user@ragagent.com",
                "password": "user123",
                "role": "user",
                "created_at": datetime.now() - timedelta(days=25)
            }
        ]

    def get_repositories(self) -> List[Dict[str, Any]]:
        return self.repositories

    def get_repository(self, repo_id: str) -> Dict[str, Any]:
        return next((repo for repo in self.repositories if repo["id"] == repo_id), None)

    def get_chat_rooms(self, repo_id: str) -> List[Dict[str, Any]]:
        return [room for room in self.chat_rooms if room["repository_id"] == repo_id]

    def get_messages(self, chat_room_id: str) -> List[Dict[str, Any]]:
        return [msg for msg in self.messages if msg["chat_room_id"] == chat_room_id]

    def get_vectordb_collections(self, repo_id: str) -> List[Dict[str, Any]]:
        return [col for col in self.vectordb_collections if col["repository_id"] == repo_id]

    def get_repository_members(self, repo_id: str) -> List[Dict[str, Any]]:
        return [member for member in self.repository_members if member["repository_id"] == repo_id]

    def add_message(self, chat_room_id: str, sender: str, content: str) -> Dict[str, Any]:
        new_message = {
            "id": str(len(self.messages) + 1),
            "chat_room_id": chat_room_id,
            "sender": sender,
            "content": content,
            "timestamp": datetime.now()
        }
        self.messages.append(new_message)
        return new_message

    def create_chat_room(self, name: str, repo_id: str) -> Dict[str, Any]:
        new_room = {
            "id": str(len(self.chat_rooms) + 1),
            "name": name,
            "repository_id": repo_id,
            "created_at": datetime.now(),
            "last_message": "",
            "message_count": 0
        }
        self.chat_rooms.append(new_room)
        return new_room

    def get_user_active_chats_count(self, user_email: str) -> int:
        user_repos = []
        if user_email == "admin@ragagent.com":
            user_repos = ["1", "2", "3"]
        elif user_email == "user@ragagent.com":
            user_repos = ["1", "2"]
        else:
            user_repos = ["1"]

        user_chat_rooms = [room for room in self.chat_rooms if room["repository_id"] in user_repos]
        return len(user_chat_rooms)

    def get_user_recent_activity(self, user_email: str) -> List[Dict[str, Any]]:
        if user_email == "admin@ragagent.com":
            return [
                {"type": "chat", "message": "New question in awesome-ml-project", "time": "2 min ago"},
                {"type": "sync", "message": "microservices-api synchronized", "time": "1 hour ago"},
                {"type": "member", "message": "New member joined react-dashboard", "time": "3 hours ago"},
                {"type": "collection", "message": "Vector collection updated", "time": "1 day ago"}
            ]
        else:
            return [
                {"type": "chat", "message": "Asked about authentication system", "time": "1 hour ago"},
                {"type": "chat", "message": "Discussion in react-dashboard", "time": "2 hours ago"},
                {"type": "collection", "message": "Accessed code embeddings", "time": "1 day ago"}
            ]

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증"""
        user = next((u for u in self.users if u["email"] == email and u["password"] == password), None)
        if user:
            # 패스워드 제외하고 반환
            user_data = user.copy()
            del user_data["password"]
            return user_data
        return None

    def create_user(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """새 사용자 생성"""
        # 이메일 중복 확인
        if any(u["email"] == email for u in self.users):
            raise ValueError("Email already exists")

        new_user = {
            "id": str(len(self.users) + 1),
            "username": username,
            "email": email,
            "password": password,
            "role": "user",
            "created_at": datetime.now()
        }
        self.users.append(new_user)

        # 패스워드 제외하고 반환
        user_data = new_user.copy()
        del user_data["password"]
        return user_data

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        user = next((u for u in self.users if u["email"] == email), None)
        if user:
            user_data = user.copy()
            del user_data["password"]
            return user_data
        return None

# Global instance
data_service = DummyDataService()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "RAG Agent Gateway API", "version": "1.0.0"}

@app.get("/repositories")
async def get_repositories():
    return jsonable_encoder(data_service.get_repositories())

@app.get("/repositories/{repo_id}")
async def get_repository(repo_id: str):
    repo = data_service.get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return jsonable_encoder(repo)

@app.get("/repositories/{repo_id}/chat-rooms")
async def get_chat_rooms(repo_id: str):
    return jsonable_encoder(data_service.get_chat_rooms(repo_id))

@app.get("/chat-rooms/{chat_room_id}/messages")
async def get_messages(chat_room_id: str):
    return jsonable_encoder(data_service.get_messages(chat_room_id))

@app.post("/chat-rooms/{chat_room_id}/messages")
async def add_message(chat_room_id: str, message_request: MessageRequest):
    # 실제 RAG 처리는 나중에 구현, 지금은 더미 응답
    user_message = data_service.add_message(
        chat_room_id,
        message_request.sender,
        message_request.content
    )

    # 봇 응답 생성 (더미)
    bot_response = data_service.add_message(
        chat_room_id,
        "bot",
        f"I understand your question about '{message_request.content}'. This is a placeholder response that will be replaced with actual RAG processing."
    )

    return jsonable_encoder({"user_message": user_message, "bot_response": bot_response})

@app.post("/repositories/{repo_id}/chat-rooms")
async def create_chat_room(repo_id: str, room_request: ChatRoomRequest):
    return jsonable_encoder(data_service.create_chat_room(room_request.name, repo_id))

@app.get("/repositories/{repo_id}/vectordb/collections")
async def get_vectordb_collections(repo_id: str):
    return jsonable_encoder(data_service.get_vectordb_collections(repo_id))

@app.get("/repositories/{repo_id}/members")
async def get_repository_members(repo_id: str):
    return jsonable_encoder(data_service.get_repository_members(repo_id))

@app.get("/users/{user_email}/active-chats-count")
async def get_user_active_chats_count(user_email: str):
    count = data_service.get_user_active_chats_count(user_email)
    return {"count": count}

@app.get("/users/{user_email}/recent-activity")
async def get_user_recent_activity(user_email: str):
    activities = data_service.get_user_recent_activity(user_email)
    return jsonable_encoder({"activities": activities})

# 인증 API 엔드포인트 (백엔드 프록시)
@app.post("/auth/login")
async def login(login_request: LoginRequest):
    """로그인 요청을 백엔드로 프록시"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": login_request.email, "password": login_request.password},
                headers={"Content-Type": "application/json"},
                timeout=3.0
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            else:
                raise HTTPException(status_code=response.status_code, detail="Backend authentication failed")

        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Backend service unavailable")

@app.post("/auth/signup")
async def signup(signup_request: SignupRequest):
    """회원가입 요청을 백엔드로 프록시"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/auth/signup",
                json={
                    "email": signup_request.email,
                    "password": signup_request.password,
                    "username": signup_request.username
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Registration failed")
                raise HTTPException(status_code=400, detail=error_detail)
            else:
                raise HTTPException(status_code=response.status_code, detail="Backend registration failed")

        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Backend service unavailable")

@app.get("/auth/user/{email}")
async def get_user_by_email(email: str):
    """사용자 조회 - 일단 더미 데이터 사용 (나중에 백엔드 연동)"""
    user = data_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return jsonable_encoder(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)