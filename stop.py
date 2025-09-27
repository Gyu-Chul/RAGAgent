#!/usr/bin/env python3
"""
RAG Agent 통합 종료 스크립트
"""

from scripts.process_manager import ProcessManager

if __name__ == "__main__":
    manager = ProcessManager()
    manager.stop_all_services()