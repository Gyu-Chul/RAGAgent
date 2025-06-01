# backend/src/file_flag/file_flag.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime
import json
from task_queue import task_queue

router = APIRouter()

class TaskCreate(BaseModel):
    type:    str = Field(..., example="MyType")
    content: str = Field(..., example="payload")
    name:    str = Field("None", example="TASK_NAME")

@router.post("/test1", status_code=201)
async def add_task(payload: TaskCreate):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_task = {
        "id": None,
        "status": "PENDING",
        "type": payload.type,
        "content": payload.content,
        "name": payload.name,
        "created_date": now
    }

    task_queue.append(new_task)
    print(task_queue)
    return 1

@router.get("/test2")
def get_last_task():
    tasks = _load_tasks()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found.")
    return tasks[-1]
