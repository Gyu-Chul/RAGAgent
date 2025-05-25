# file_flag_bridge.py

import json
import time
import os
from typing import Optional, Dict, Any
from datetime import datetime
class FileFlagBridge:

    def __init__(self, flag_path: str, interval: float = 5.0):
        self.flag_path = flag_path
        self.interval = interval
        self._last_seen_id: Optional[Any] = None
        self._running = False

    def _read_last_flag(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.flag_path):
            return None

        try:
            with open(self.flag_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data[-1]
        except Exception as e:
            print(f"[Warning] flag 파일 읽기 오류: {e}")
        return None

    def _handle_flag(self, flag: Dict[str, Any]):
        print(f"[Info] 처리할 flag 발견: {flag}")
        if flag['status'] == 'PENDING':
            print("마지막 Task는 비정상적으로 종료되었습니다.")
        elif flag['status'] == 'SUCCESS':
            print("파일 정상 인식완료.")
        elif flag['status'] == 'FAIL':
            print("파일 정상 인식완료.")

    def start_polling(self):
        print(f"[Start] {self.flag_path} 파일 폴링(주기: {self.interval}s) 시작")
        self._running = True
        try:
            while self._running:
                flag = self._read_last_flag()
                if flag:
                    current_id = flag.get('id')
                    if current_id != self._last_seen_id:
                        self._last_seen_id = current_id
                        self._handle_flag(flag)
                    else:
                        now = datetime.now()
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 추가된 Task 가 없습니다.")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n[Stop] 사용자의 요청으로 폴링을 종료합니다.")
        finally:
            self._cleanup()

    def stop(self):
        self._running = False

    def _cleanup(self):
        print("[Cleanup] 리소스 정리 중...")
        
        
        # 혹시 모를 종료 로직 추가 예정
        print("[Cleanup] 완료.")

if __name__ == "__main__":
    bridge = FileFlagBridge(flag_path="task.flag.json", interval=5.0)
    bridge.start_polling()
