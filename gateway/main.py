import logging
import os
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import httpx
from decouple import Config, RepositoryEnv

# .env.local 파일이 있으면 우선 사용 (로컬 개발용)
env_local_path = Path(__file__).parent.parent / '.env.local'
if env_local_path.exists():
    config = Config(RepositoryEnv(str(env_local_path)))
    BACKEND_URL = config("BACKEND_URL", default="http://localhost:8001")
    CORS_ORIGINS_STR = config("CORS_ORIGINS", default='["http://localhost:8000"]')
    CORS_ORIGINS = eval(CORS_ORIGINS_STR)
else:
    # .env.local이 없으면 환경변수 또는 기본값 사용
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
    CORS_ORIGINS = eval(os.getenv("CORS_ORIGINS", '["http://localhost:8000"]'))

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


# 백엔드로 프록시하는 catch-all 라우트
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(request: Request, path: str):
    """모든 /api/* 요청을 백엔드로 프록시"""
    # 백엔드 URL 생성
    url = f"{BACKEND_URL}/api/{path}"

    # 쿼리 파라미터 추가
    if request.url.query:
        url = f"{url}?{request.url.query}"

    # 요청 헤더 복사
    headers = dict(request.headers)
    headers.pop("host", None)  # Host 헤더 제거

    # 요청 본문 읽기
    body = await request.body()

    logging.info(f"Proxying {request.method} request to {url}")
    logging.info(f"Request body: {body.decode('utf-8') if body else 'empty'}")

    # httpx로 백엔드에 요청 (리다이렉트 비활성화)
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                timeout=30.0
            )

            logging.info(f"Backend response status: {response.status_code}")

            # 307 리다이렉트 처리: 헤더를 유지하면서 리다이렉트 URL로 재요청
            if response.status_code in (307, 308):
                redirect_url = response.headers.get("location")
                if redirect_url:
                    logging.info(f"Following redirect to {redirect_url}")
                    # 상대 URL을 절대 URL로 변환
                    if redirect_url.startswith("/"):
                        redirect_url = f"{BACKEND_URL}{redirect_url}"

                    response = await client.request(
                        method=request.method,
                        url=redirect_url,
                        headers=headers,
                        content=body,
                        timeout=30.0
                    )
                    logging.info(f"Redirect response status: {response.status_code}")

            if response.status_code >= 400:
                logging.error(f"Backend error response: {response.text}")

            # 응답 반환
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:
            logging.error(f"Error proxying to backend: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)