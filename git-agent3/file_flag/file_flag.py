# file_flag/bridge.py
import time
import logging
from typing import Optional, Dict, Any, Protocol
from .reader import read_last_flag

class FlagHandler(Protocol):
    def handle(self, flag: Dict[str, Any]) -> None:
        ...

class FileFlag:
    def __init__(
        self,
        flag_path: str,
        interval: float,
        handler: FlagHandler
    ):
        self.flag_path = flag_path
        self.interval = interval
        self.handler = handler
        self._last_id: Optional[Any] = None
        self._running = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def start_polling(self):
        self._running = True
        self.logger.info(f"Polling 시작: {self.flag_path} (주기 {self.interval}s)")
        try:
            while self._running:
                flag = read_last_flag(self.flag_path)
                if flag:
                    curr = flag.get("id")
                    if curr != self._last_id:
                        self._last_id = curr
                        self.logger.info(f"새 Task 감지: {flag}")
                        self.handler.handle(flag)
                    else:
                        ts = time.strftime("%Y-%m-%d %H:%M:%S")
                        self.logger.debug(f"[{ts}] 추가된 Task 가 없습니다.")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt 감지 — 폴링 중단")
        finally:
            self._cleanup()

    def stop(self):
        self._running = False

    def _cleanup(self):
        self.logger.info("리소스 정리 완료")
