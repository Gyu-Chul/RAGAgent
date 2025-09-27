#!/usr/bin/env python3
"""
RAG Agent 통합 시작 스크립트
"""

from scripts.process_manager import ProcessManager

if __name__ == "__main__":
    manager = ProcessManager()
    manager.start_all_services()

    try:
        # 메인 프로세스가 종료되지 않도록 대기
        print("Ctrl+C를 눌러 모든 서비스를 종료할 수 있습니다.")
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_all_services()