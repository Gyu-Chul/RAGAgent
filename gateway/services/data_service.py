from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

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
                "content": "Based on the repository code, the transformer architecture is implemented...",
                "timestamp": datetime.now() - timedelta(minutes=9),
                "sources": ["models/transformer.py", "config/model_config.yaml", "docs/architecture.md"]
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
            }
        ]

        self.users = [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@ragagent.com",
                "password": "admin123",
                "role": "admin",
                "created_at": datetime.now() - timedelta(days=30)
            }
        ]

    def get_repositories(self) -> List[Dict[str, Any]]:
        return self.repositories

    def get_repository(self, repo_id: str) -> Optional[Dict[str, Any]]:
        return next((repo for repo in self.repositories if repo["id"] == repo_id), None)

    def get_chat_rooms(self, repository_id: str) -> List[Dict[str, Any]]:
        return [room for room in self.chat_rooms if room["repository_id"] == repository_id]

    def get_messages(self, chat_room_id: str) -> List[Dict[str, Any]]:
        return [msg for msg in self.messages if msg["chat_room_id"] == chat_room_id]

    def get_vectordb_collections(self, repository_id: str) -> List[Dict[str, Any]]:
        return [col for col in self.vectordb_collections if col["repository_id"] == repository_id]

    def get_repository_members(self, repository_id: str) -> List[Dict[str, Any]]:
        return [member for member in self.repository_members if member["repository_id"] == repository_id]

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = next((u for u in self.users if u["email"] == email and u["password"] == password), None)
        if user:
            return {k: v for k, v in user.items() if k != "password"}
        return None