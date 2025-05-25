# handlers/flag_handler.py
import logging
from typing import Dict, Any

class DefaultFlagHandler:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def handle(self, flag: Dict[str, Any]) -> None:
        status = flag.get("status")
        name   = flag.get("name")
        # 예시 처리
        if status == "PENDING":
            self.logger.info(f"처리 대기: {name}")
        elif status == "SUCCESS":
            self.logger.info(f"성공 완료: {name}")
        elif status == "FAIL":
            self.logger.error(f"실패 알림: {name}")
        else:
            self.logger.warning(f"알 수 없는 상태({status}): {name}")
