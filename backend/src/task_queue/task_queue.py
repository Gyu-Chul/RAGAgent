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

def _create_tasks(payload) -> dict:
    """
    payload: 사용자로부터 받은 작업 정보 (payload.type, payload.content, payload.name 등 포함)
    """
    # 파일에 저장된 기존 task 목록 불러오기
    tasks = _load_tasks()

    # 마지막 task 상태가 아직 PENDING이면 새로 추가 불가
    if tasks and tasks[-1].get("status") == "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Previous task is still PENDING. Cannot add new task."
        )

    # 새로운 task 객체 생성, id는 None 상태로 대기
    now = datetime.now().isoformat()
    new_task = {
        "id": None,
        "status": "PENDING",
        "type": payload.type,
        "content": payload.content,
        "name": payload.name,
        "created_date": now
    }

    # 메모리 큐에 추가 (id는 아직 할당 안 된 상태)
    task_queue.append(new_task)

    return {"detail": "Task enqueued. Processing will start shortly."}


def task_worker():
    while True:
        if task_queue:
            task = task_queue[0]

            # 아직 파일에 기록되지 않은 새 작업
            if task.get("id") is None:
                # 파일에 있는 작업 목록 로드
                tasks_on_disk = _load_tasks()
                # 다음 id 계산
                next_id = 1 if not tasks_on_disk else tasks_on_disk[-1].get("id", 0) + 1

                # 메모리 작업 객체에 id 할당
                task["id"] = next_id

                # 파일에 저장할 작업 객체 복사
                task_record = {
                    "id": task["id"],
                    "status": task["status"],
                    "type": task["type"],
                    "content": task["content"],
                    "name": task["name"],
                    "created_date": task["created_date"]
                }
                # 디스크에 기록
                tasks_on_disk.append(task_record)
                _save_tasks(tasks_on_disk)

            else:
                # 이미 id가 할당된 작업의 상태를 파일에서 확인하려면 파일 로드
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