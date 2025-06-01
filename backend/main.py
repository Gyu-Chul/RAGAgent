import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from fastapi import FastAPI
from task_queue import task_queue
from sample import router as sample_router
from file_flag import router as file_flag_router

app = FastAPI(
    title="GitAI Backend",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.include_router(sample_router, prefix="/api/sample")
app.include_router(file_flag_router, prefix="/api/file_flag")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
