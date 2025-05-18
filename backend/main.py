import sys
from pathlib import Path

# src 디렉토리를 모듈 경로에 추가
BASE_DIR = Path(__file__).parent / "src"
sys.path.append(str(BASE_DIR))

from fastapi import FastAPI
from sample.sample import router as sample_router

app = FastAPI(
    title="GitAI Backend",
    version="0.1.0",
    docs_url="/api/docs",       # Swagger UI
    openapi_url="/api/openapi.json"
)

# 모든 /api/sample1, /api/sample2 호출은 아래 라우터로 전달
app.include_router(sample_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
