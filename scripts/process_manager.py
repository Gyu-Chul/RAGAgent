#!/usr/bin/env python3
"""
RAGIT Process Manager - 리팩토링된 버전
단일 책임 원칙과 인터페이스 분리 원칙을 준수하여 설계
"""

import os
import sys
import signal
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse


class ServiceConfig:
    """서비스 설정 관리 클래스"""

    def __init__(self, project_root: Path) -> None:
        self.project_root: Path = project_root
        self.services: Dict[str, Dict[str, Any]] = {
            'backend': {
                'dir': self.project_root / 'backend',
                'cmd': [sys.executable, '-c', 'import uvicorn; uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)'],
                'port': 8001,
                'description': 'Backend API Server'
            },
            'frontend': {
                'dir': self.project_root / 'frontend',
                'cmd': [sys.executable, 'main.py'],
                'port': 8000,
                'description': 'Frontend Web Interface'
            },
            'gateway': {
                'dir': self.project_root / 'gateway',
                'cmd': [sys.executable, 'main.py'],
                'port': 8080,
                'description': 'API Gateway'
            },
            'rag_worker': {
                'dir': self.project_root / 'rag_worker',
                'cmd': ['celery', '-A', 'main', 'worker', '--loglevel=info', '-P', 'solo'],
                'port': None,
                'description': 'RAG Worker Process'
            }
        }

    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """서비스 설정 조회"""
        return self.services.get(service_name)

    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """모든 서비스 설정 조회"""
        return self.services

    def service_exists(self, service_name: str) -> bool:
        """서비스 존재 여부 확인"""
        return service_name in self.services


class ProcessMonitor:
    """프로세스 출력 모니터링 클래스"""

    def monitor_process_output(self, service_name: str, process: subprocess.Popen) -> None:
        """프로세스 출력 모니터링"""
        def read_output(stream: Any, prefix: str) -> None:
            for line in iter(stream.readline, ''):
                if line.strip():
                    print(f"[{service_name}] {line.strip()}")

        # stdout과 stderr를 별도 스레드에서 처리
        stdout_thread = threading.Thread(
            target=read_output,
            args=(process.stdout, "OUT"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=read_output,
            args=(process.stderr, "ERR"),
            daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()


class ServiceController:
    """개별 서비스 제어 클래스"""

    def __init__(self, config: ServiceConfig, monitor: ProcessMonitor) -> None:
        self.config: ServiceConfig = config
        self.monitor: ProcessMonitor = monitor
        self.processes: Dict[str, subprocess.Popen] = {}

    def start_service(self, service_name: str) -> bool:
        """개별 서비스 시작"""
        if not self.config.service_exists(service_name):
            print(f"[ERROR] 알 수 없는 서비스: {service_name}")
            return False

        if service_name in self.processes and self.processes[service_name].poll() is None:
            print(f"⚠️  {service_name}이 이미 실행 중입니다.")
            return True

        service = self.config.get_service(service_name)
        if not service:
            return False

        print(f"[START] {service['description']} 시작 중...")

        try:
            process = subprocess.Popen(
                service['cmd'],
                cwd=service['dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.processes[service_name] = process

            # 출력 모니터링을 위한 별도 스레드
            threading.Thread(
                target=self.monitor.monitor_process_output,
                args=(service_name, process),
                daemon=True
            ).start()

            # 잠시 대기하여 프로세스가 제대로 시작되는지 확인
            time.sleep(1)
            if process.poll() is None:
                port_info = f" (포트: {service['port']})" if service['port'] else ""
                print(f"[SUCCESS] {service['description']} 시작됨{port_info}")
                return True
            else:
                print(f"[FAILED] {service['description']} 시작 실패")
                return False

        except Exception as e:
            print(f"[ERROR] {service['description']} 시작 중 오류: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """개별 서비스 종료"""
        if service_name not in self.processes:
            print(f"⚠️  {service_name}이 실행 중이지 않습니다.")
            return True

        process = self.processes[service_name]
        service = self.config.get_service(service_name)
        if not service:
            return False

        print(f"🛑 {service['description']} 종료 중...")

        try:
            # 정상 종료 시도
            process.terminate()

            # 5초 대기
            try:
                process.wait(timeout=5)
                print(f"[SUCCESS] {service['description']} 정상 종료됨")
            except subprocess.TimeoutExpired:
                # 강제 종료
                process.kill()
                process.wait()
                print(f"⚠️  {service['description']} 강제 종료됨")

            del self.processes[service_name]
            return True

        except Exception as e:
            print(f"[ERROR] {service['description']} 종료 중 오류: {e}")
            return False

    def restart_service(self, service_name: str) -> None:
        """개별 서비스 재시작"""
        print(f"🔄 {service_name} 재시작 중...")
        self.stop_service(service_name)
        time.sleep(2)
        self.start_service(service_name)

    def is_service_running(self, service_name: str) -> bool:
        """서비스 실행 상태 확인"""
        return (service_name in self.processes and
                self.processes[service_name].poll() is None)


class SystemOrchestrator:
    """시스템 전체 오케스트레이션 클래스"""

    def __init__(self, controller: ServiceController, config: ServiceConfig) -> None:
        self.controller: ServiceController = controller
        self.config: ServiceConfig = config

    def start_all_services(self) -> bool:
        """모든 서비스 시작"""
        print("RAGIT 전체 시스템 시작 중...")
        print("=" * 50)

        # 시작 순서: gateway -> backend -> rag_worker -> frontend
        start_order = ['gateway', 'backend', 'rag_worker', 'frontend']

        for service_name in start_order:
            if not self.controller.start_service(service_name):
                print(f"[ERROR] {service_name} 시작 실패로 인해 전체 시작을 중단합니다.")
                self.stop_all_services()
                return False
            time.sleep(2)  # 각 서비스 간 시작 간격

        print("=" * 50)
        print("[SUCCESS] 모든 서비스가 성공적으로 시작되었습니다!")
        print("\n서비스 상태:")
        self.show_status()
        return True

    def stop_all_services(self) -> None:
        """모든 서비스 종료"""
        print("🛑 모든 서비스 종료 중...")
        print("=" * 50)

        # 종료 순서: frontend -> rag_worker -> backend -> gateway
        stop_order = ['frontend', 'rag_worker', 'backend', 'gateway']

        for service_name in stop_order:
            if self.controller.is_service_running(service_name):
                self.controller.stop_service(service_name)
                time.sleep(1)

        print("=" * 50)
        print("[SUCCESS] 모든 서비스가 종료되었습니다.")

    def show_status(self) -> None:
        """현재 실행 중인 서비스 상태 표시"""
        print("\n[STATUS] 서비스 상태:")
        print("-" * 40)

        for service_name, service in self.config.get_all_services().items():
            if self.controller.is_service_running(service_name):
                status = "[RUNNING] 실행중"
                port_info = f" (포트: {service['port']})" if service['port'] else ""
            else:
                status = "[STOPPED] 중지됨"
                port_info = ""

            print(f"{service['description']:<20} {status}{port_info}")

    def monitor_services(self) -> None:
        """서비스 모니터링 모드"""
        print("👁️  서비스 모니터링 모드 시작 (Ctrl+C로 종료)")
        print("=" * 50)

        try:
            while True:
                self.show_status()
                time.sleep(10)
                print("\n" + "=" * 50)
        except KeyboardInterrupt:
            print("\n모니터링을 종료합니다.")


class SignalHandler:
    """시그널 처리 클래스"""

    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self.orchestrator: SystemOrchestrator = orchestrator
        self.setup_signal_handlers()

    def setup_signal_handlers(self) -> None:
        """프로세스 종료 시그널 핸들러 설정"""
        def signal_handler(signum: int, frame: Any) -> None:
            print("\n프로세스 종료 신호를 받았습니다. 모든 서비스를 종료합니다...")
            self.orchestrator.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)


class ProcessManager:
    """메인 프로세스 매니저 - 의존성 조립 및 파사드 역할"""

    def __init__(self) -> None:
        project_root = Path(__file__).parent.parent

        # 의존성 조립
        self.config = ServiceConfig(project_root)
        self.monitor = ProcessMonitor()
        self.controller = ServiceController(self.config, self.monitor)
        self.orchestrator = SystemOrchestrator(self.controller, self.config)
        self.signal_handler = SignalHandler(self.orchestrator)

    def start_service(self, service_name: str) -> bool:
        """개별 서비스 시작"""
        return self.controller.start_service(service_name)

    def stop_service(self, service_name: str) -> bool:
        """개별 서비스 종료"""
        return self.controller.stop_service(service_name)

    def restart_service(self, service_name: str) -> None:
        """개별 서비스 재시작"""
        self.controller.restart_service(service_name)

    def start_all_services(self) -> bool:
        """모든 서비스 시작"""
        return self.orchestrator.start_all_services()

    def stop_all_services(self) -> None:
        """모든 서비스 종료"""
        self.orchestrator.stop_all_services()

    def show_status(self) -> None:
        """서비스 상태 표시"""
        self.orchestrator.show_status()

    def monitor_services(self) -> None:
        """서비스 모니터링"""
        self.orchestrator.monitor_services()


def main() -> None:
    """메인 함수"""
    parser = argparse.ArgumentParser(description='RAGIT Process Manager')
    parser.add_argument('action', nargs='?', choices=[
        'start-all', 'stop-all', 'status', 'monitor',
        'start-backend', 'start-frontend', 'start-gateway', 'start-rag-worker',
        'stop-backend', 'stop-frontend', 'stop-gateway', 'stop-rag-worker',
        'restart-backend', 'restart-frontend', 'restart-gateway', 'restart-rag-worker'
    ], default='start-all', help='실행할 액션')

    args = parser.parse_args()
    manager = ProcessManager()

    if args.action == 'start-all':
        manager.start_all_services()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_all_services()

    elif args.action == 'stop-all':
        manager.stop_all_services()

    elif args.action == 'status':
        manager.show_status()

    elif args.action == 'monitor':
        manager.monitor_services()

    elif args.action.startswith('start-'):
        service = args.action.replace('start-', '').replace('-', '_')
        manager.start_service(service)

    elif args.action.startswith('stop-'):
        service = args.action.replace('stop-', '').replace('-', '_')
        manager.stop_service(service)

    elif args.action.startswith('restart-'):
        service = args.action.replace('restart-', '').replace('-', '_')
        manager.restart_service(service)


# CLI 진입점 함수들
def start_all() -> None:
    """모든 서비스 시작"""
    manager = ProcessManager()
    manager.start_all_services()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_all_services()


def stop_all() -> None:
    """모든 서비스 종료"""
    manager = ProcessManager()
    manager.stop_all_services()


def start_backend() -> None:
    """백엔드 서비스 시작"""
    manager = ProcessManager()
    manager.start_service('backend')


def start_frontend() -> None:
    """프론트엔드 서비스 시작"""
    manager = ProcessManager()
    manager.start_service('frontend')


def start_gateway() -> None:
    """게이트웨이 서비스 시작"""
    manager = ProcessManager()
    manager.start_service('gateway')


def start_rag_worker() -> None:
    """RAG 워커 서비스 시작"""
    manager = ProcessManager()
    manager.start_service('rag_worker')


if __name__ == "__main__":
    main()