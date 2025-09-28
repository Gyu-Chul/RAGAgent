from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from typing import Dict, Any, List

import os
from typing import List

# 환경변수에서 직접 읽기
CORS_ORIGINS: List[str] = eval(os.getenv("CORS_ORIGINS", '["http://localhost:8000"]'))
from .routers import auth
from .services.data_service import DummyDataService

# Gateway App
app = FastAPI(title="RAG Agent Gateway", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)

# 데이터 서비스 인스턴스
data_service = DummyDataService()

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "RAG Agent Gateway", "version": "1.0.0"}

@app.get("/repositories")
async def get_repositories() -> List[Dict[str, Any]]:
    repositories = data_service.get_repositories()
    return jsonable_encoder(repositories)

@app.get("/repositories/{repository_id}/chat-rooms")
async def get_chat_rooms(repository_id: str) -> List[Dict[str, Any]]:
    chat_rooms = data_service.get_chat_rooms(repository_id)
    return jsonable_encoder(chat_rooms)

@app.get("/chat-rooms/{chat_room_id}/messages")
async def get_messages(chat_room_id: str) -> List[Dict[str, Any]]:
    messages = data_service.get_messages(chat_room_id)
    return jsonable_encoder(messages)

@app.get("/repositories/{repository_id}/vectordb/collections")
async def get_vectordb_collections(repository_id: str) -> List[Dict[str, Any]]:
    collections = data_service.get_vectordb_collections(repository_id)
    return jsonable_encoder(collections)

@app.get("/repositories/{repository_id}/members")
async def get_repository_members(repository_id: str) -> List[Dict[str, Any]]:
    members = data_service.get_repository_members(repository_id)
    return jsonable_encoder(members)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)