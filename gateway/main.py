import logging
import os
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

# 게이트웨이 로깅 설정
def setup_logging() -> None:
    """게이트웨이 프로세스 자체 로그 캡처를 위한 설정"""
    from datetime import datetime

    # 현재 날짜로 디렉토리 생성
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs") / today
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로그 파일 경로
    log_file = log_dir / f"gateway_{datetime.now().strftime('%H-%M-%S')}.log"

    # uvicorn과 FastAPI 자체 로그를 파일로 리다이렉트
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 기본 포맷 (프로세스 자체 로그 유지)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # 루트 로거에 파일 핸들러 추가 (모든 로그를 파일로)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # uvicorn 로거에 파일 핸들러 추가
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.addHandler(file_handler)

    # FastAPI 접근 로그 활성화
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addHandler(file_handler)

# 로깅 초기화
setup_logging()

# 환경변수에서 직접 읽기
CORS_ORIGINS: List[str] = eval(os.getenv("CORS_ORIGINS", '["http://localhost:8000"]'))
from .routers import auth
from .services.data_service import DummyDataService

# Gateway App
app = FastAPI(title="RAG Agent Gateway", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    pass

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

@app.get("/repositories/{repository_id}")
async def get_repository(repository_id: str) -> Dict[str, Any]:
    """특정 Repository 정보 조회"""
    repositories = data_service.get_repositories()
    for repo in repositories:
        if repo['id'] == repository_id:
            return jsonable_encoder(repo)
    # Repository가 없으면 404 대신 기본 데이터 반환
    return jsonable_encoder({
        "id": repository_id,
        "name": f"Repository {repository_id}",
        "description": "Repository description",
        "url": f"https://github.com/example/repo{repository_id}",
        "status": "active"
    })

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