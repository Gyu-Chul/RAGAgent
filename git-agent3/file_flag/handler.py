# handlers/flag_handler.py

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dummy.dummy import dummy


# 1) Path 객체로 선언
#    현재 파일 위치 기준으로 git-ai/git-agent3/task.flag.json 을 가리키도록
TASK_FILE = (
    Path(__file__).resolve()
    .parents[1]          # handlers/ -> git-agent3/
    / "task.flag.json"
)

class DefaultFlagHandler:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def handle(self, flag: Dict[str, Any]) -> None:
        status = flag.get("status")
        name   = flag.get("name")
        task_id= flag.get("id")
        type   = flag.get("type")

        if status == "PENDING":
            self.logger.info(f"[PENDING → SUCCESS] Task {task_id} ({name}) 상태 변경 중")

            # 2) Path.read_text() 사용
            try:
                tasks = json.loads(TASK_FILE.read_text(encoding="utf-8"))
            except FileNotFoundError:
                self.logger.error(f"플래그 파일을 찾을 수 없습니다: {TASK_FILE}")
                return
            except json.JSONDecodeError as e:
                self.logger.error(f"플래그 파일 파싱 오류: {e}")
                return

            # 3) 상태 업데이트
            updated = False
            for t in tasks:
                # 현재 상태 업데이트 로직은, handle 함수 호출시 들어온 id 값과 이 스크립트에서 파일을 다시 읽은 뒤 id를 조회하여
                # 가져오는 방식임.
                if t.get("id") == task_id:
                    t["status"] = dummy()
                    t["updated_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updated = True
                    break

            if not updated:
                self.logger.warning(f"ID={task_id} 인 Task를 찾지 못했습니다.")
                return

            # 4) Path.write_text() 로 덮어쓰기
            try:
                TASK_FILE.write_text(
                    json.dumps(tasks, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                self.logger.info(f"Task {task_id} 상태를 SUCCESS 로 저장했습니다.")
            except Exception as e:
                self.logger.error(f"플래그 파일 저장 중 오류: {e}")

        elif status == "SUCCESS":
            self.logger.info(f"성공 완료: {name}")
        elif status == "FAIL":
            self.logger.error(f"실패 알림: {name}")
        else:
            self.logger.warning(f"알 수 없는 상태({status}): {name}")
