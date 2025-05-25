# backend/src/file_flag/file_flag.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime
import json

router = APIRouter()

FLAG_FILE = (
    Path(__file__).resolve()
    .parents[3]            # git-ai 루트
    / "git-agent3"         # 형제 디렉토리
    / "task.flag.json"
)

def _load_tasks() -> list[dict]:
    if not FLAG_FILE.exists():
        return []
    with FLAG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_tasks(tasks: list[dict]) -> None:
    with FLAG_FILE.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

class TaskCreate(BaseModel):
    type:    str = Field(..., example="MyType")
    content: str = Field(..., example="payload")
    name:    str = Field("None", example="TASK_NAME")

@router.post("/test1", status_code=201)
async def add_task(payload: TaskCreate):

    tasks = _load_tasks()

    if tasks and tasks[-1].get("status") == "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Previous task is still PENDING. Cannot add new task."
        )

    next_id = 1 if not tasks else tasks[-1].get("id", 0) + 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_task = {
        "id": next_id,
        "status": "PENDING",
        "type": payload.type,
        "content": payload.content,
        "name": payload.name,
        "created_date": now
    }

    tasks.append(new_task)
    _save_tasks(tasks)
    return new_task

@router.get("/test2")
def get_last_task():
    tasks = _load_tasks()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found.")
    return tasks[-1]
