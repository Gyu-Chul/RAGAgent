from datetime import datetime, timedelta
from typing import List, Dict, Any

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
                "email": "admin@ragit.com",
                "joined_at": datetime.now() - timedelta(days=30)
            },
            {
                "id": "2",
                "repository_id": "1",
                "user_id": "2",
                "username": "user",
                "role": "member",
                "email": "user@ragit.com",
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
        """Get the count of active chat rooms for a specific user"""
        user_repos = []
        if user_email == "admin@ragit.com":
            user_repos = ["1", "2", "3"]  # Admin has access to all repos
        elif user_email == "user@ragit.com":
            user_repos = ["1", "2"]  # Regular user has access to specific repos
        else:
            user_repos = ["1"]  # Default access

        user_chat_rooms = [room for room in self.chat_rooms if room["repository_id"] in user_repos]
        return len(user_chat_rooms)

    def get_user_recent_activity(self, user_email: str) -> List[Dict[str, Any]]:
        """Get user-specific recent activity"""
        if user_email == "admin@ragit.com":
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