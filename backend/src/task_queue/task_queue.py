import threading
import time
import json
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException

# 글로벌 작업 큐
task_queue = []

FLAG_FILE = (
    Path(__file__).resolve()
    .parents[3]            # git-ai 루트
    / "git-agent"         # 형제 디렉토리
    / "task.flag.json"
)

async def create_tasks(new_task):
    tasks_on_disk = _load_tasks()

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

def _load_tasks() -> list[dict]:
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
            tasks_on_disk = _load_tasks()
            # 해당 작업의 최신 상태 찾기
            matching = next((t for t in tasks_on_disk if t["id"] == task["id"]), None)
            if matching:
                current_status = matching.get("status")
            else:
                current_status = task.get("status")

            # 작업 상태가 여전히 PENDING이면 대기, 아니면 큐에서 제거
            if current_status != "PENDING":
                task_queue.pop(0)
                # 다음 작업으로 넘어가기 위해 continue
                continue

        # 2초 대기 후 다시 체크
        time.sleep(2)


# 워커 스레드를 데몬 모드로 시작
worker_thread = threading.Thread(target=task_worker, daemon=True)
worker_thread.start()