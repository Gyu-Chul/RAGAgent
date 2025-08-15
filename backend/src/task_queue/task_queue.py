import threading
import json
import asyncio
from pydantic import BaseModel
from src.vectorDB.vectorDB import merge_json,embed_json_file,EmbedJsonRequest

from pathlib import Path

# 글로벌 작업 큐
task_queue = []

FLAG_FILE = (
    Path(__file__).resolve()
    .parents[3]            # git-ai 루트
    / "git-agent"         # 형제 디렉토리
    / "task.flag.json"
)

async def create_tasks(new_task):
    tasks_on_disk = load_tasks()

    if task_queue:
        last_task_id = task_queue[-1]["id"]
        new_task["id"] = last_task_id + 1
    else:
        new_task["id"] = 1 if not tasks_on_disk else tasks_on_disk[-1].get("id", 0) + 1

    task_record = {
        "id": new_task["id"],
        "status": new_task["status"],
        "type": new_task["type"],
        "content": new_task["content"],
        "name": new_task["name"],
        "created_date": new_task["created_date"]
    }

    tasks_on_disk.append(task_record)
    _save_flag_file(tasks_on_disk)

    task_queue.append(new_task)
    return new_task["id"]

def load_tasks() -> list[dict]:
    if not FLAG_FILE.exists():
        return []
    with FLAG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_flag_file(tasks: list[dict]) -> None:
    with FLAG_FILE.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


async def task_worker():
    while True:
        if task_queue:
            task = task_queue[0]
            tasks_on_disk = load_tasks()
            matching = next((t for t in tasks_on_disk if t["id"] == task["id"]), None)
            if matching:
                current_status = matching.get("status")
            else:
                current_status = task.get("status")

            if current_status != "PENDING":
                if matching.get("type") == "GITCLONE":
                    result = merge_json(matching.get("name"))
                    params = {
                        "json_path": result["out_path"],
                        "collection_name": "git_ai_sample", #이거 하드 코딩이라 나중에 꼭 수정해야 함.
                        "version": 1
                    }
                    request_obj = EmbedJsonRequest(**params)
                    result2 = await embed_json_file(request_obj)
                task_queue.pop(0)
                continue

        await asyncio.sleep(2)

def run_worker():
    asyncio.run(task_worker())

worker_thread = threading.Thread(target=run_worker, daemon=True)
worker_thread.start()