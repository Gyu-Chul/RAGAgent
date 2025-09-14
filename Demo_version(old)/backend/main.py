import sys
from pathlib import Path


from fastapi import FastAPI
from pymilvus import connections

from src.task_queue import task_queue
from src.file_flag import router as file_flag_router
from src.chat import router as chat_router
from src.vectorDB import router as vectorDB_router

app = FastAPI(
    title="GitAI Backend",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.include_router(file_flag_router, prefix="/api/file_flag")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(vectorDB_router, prefix="/api/vectorDB")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
