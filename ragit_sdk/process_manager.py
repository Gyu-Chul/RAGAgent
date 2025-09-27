#!/usr/bin/env python3
"""
RAGIT Process Manager SDK
단일 책임 원칙과 인터페이스 분리 원칙을 준수하여 설계된 프로세스 관리 시스템
"""

import os
import sys
import signal
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

from .config import RagitConfig
from .logger import get_service_logger, log_service_start, log_service_stop, log_service_error, log_service_ready


class ProcessMonitor:
    """프로세스 출력 모니터링 클래스"""

    def __init__(self) -> None:
        self.logger = get_service_logger("monitor")

    def monitor_process_output(self, service_name: str, process: subprocess.Popen) -> None:
        """프로세스 출력 모니터링"""
        def read_output(stream: Any, stream_type: str) -> None:
            try:
                for line in iter(stream.readline, ''):
                    if line.strip():
                        # 로그 레벨에 따라 출력
                        if "error" in line.lower() or "exception" in line.lower():
                            self.logger.error(f"[{service_name}] {line.strip()}")
                        elif "warning" in line.lower() or "warn" in line.lower():
                            self.logger.warning(f"[{service_name}] {line.strip()}")
                        else:
                            self.logger.info(f"[{service_name}] {line.strip()}")
            except Exception as e:
                self.logger.error(f"Output monitoring error for {service_name}: {e}")

        # stdout과 stderr를 별도 스레드에서 처리
        if process.stdout:
            stdout_thread = threading.Thread(
                target=read_output,
                args=(process.stdout, "OUT"),
                daemon=True
            )
            stdout_thread.start()

        if process.stderr:
            stderr_thread = threading.Thread(
                target=read_output,
                args=(process.stderr, "ERR"),
                daemon=True
            )
            stderr_thread.start()


class ServiceController:
    """개별 서비스 제어 클래스"""

    def __init__(self, config: RagitConfig, monitor: ProcessMonitor) -> None:
        self.config: RagitConfig = config
        self.monitor: ProcessMonitor = monitor
        self.processes: Dict[str, subprocess.Popen] = {}
        self.logger = get_service_logger("controller")

    def start_service(self, service_name: str) -> bool:
        """개별 서비스 시작"""
        service_config = self.config.get_service_config(service_name)
        if not service_config:
            log_service_error("controller", f"Unknown service: {service_name}")
            return False

        if service_name in self.processes and self.processes[service_name].poll() is None:
            self.logger.warning(f"{service_name} is already running")
            return True

        port = self._get_service_port(service_name)
        log_service_start(service_name, port)

        try:
            process = subprocess.Popen(
                service_config['cmd'],
                cwd=service_config['cwd'],
                env=service_config['env'],
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

            # 프로세스 시작 확인
            time.sleep(2)
            if process.poll() is None:
                url = self._get_service_url(service_name)
                log_service_ready(service_name, url)
                return True
            else:
                log_service_error("controller", f"{service_name} failed to start")
                return False

        except Exception as e:
            log_service_error("controller", f"Error starting {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """개별 서비스 종료"""
        if service_name not in self.processes:
            self.logger.warning(f"{service_name} is not running")
            return True

        process = self.processes[service_name]
        log_service_stop(service_name)

        try:
            # 정상 종료 시도
            process.terminate()

            # 5초 대기
            try:
                process.wait(timeout=5)
                self.logger.info(f"✅ {service_name} terminated gracefully")
            except subprocess.TimeoutExpired:
                # 강제 종료
                process.kill()
                process.wait()
                self.logger.warning(f"⚠️ {service_name} force killed")

            del self.processes[service_name]
            return True

        except Exception as e:
            log_service_error("controller", f"Error stopping {service_name}: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """개별 서비스 재시작"""
        self.logger.info(f"🔄 Restarting {service_name}")
        if self.stop_service(service_name):
            time.sleep(2)
            return self.start_service(service_name)
        return False

    def is_service_running(self, service_name: str) -> bool:
        """서비스 실행 상태 확인"""
        return (service_name in self.processes and
                self.processes[service_name].poll() is None)

    def get_service_pid(self, service_name: str) -> Optional[int]:
        """서비스 PID 반환"""
        if service_name in self.processes:
            return self.processes[service_name].pid
        return None

    def get_service_memory_usage(self, service_name: str) -> Optional[float]:
        """서비스 메모리 사용량 반환 (MB)"""
        pid = self.get_service_pid(service_name)
        if pid:
            try:
                process = psutil.Process(pid)
                return process.memory_info().rss / 1024 / 1024  # MB
            except psutil.NoSuchProcess:
                return None
        return None

    def _get_service_port(self, service_name: str) -> Optional[int]:
        """서비스 포트 반환"""
        port_map = {
            'frontend': self.config.frontend_port,
            'backend': self.config.backend_port,
            'gateway': self.config.gateway_port,
            'rag_worker': None
        }
        return port_map.get(service_name)

    def _get_service_url(self, service_name: str) -> Optional[str]:
        """서비스 URL 반환"""
        port = self._get_service_port(service_name)
        if port:
            return f"http://localhost:{port}"
        return None


class SystemOrchestrator:
    """시스템 전체 오케스트레이션 클래스"""

    def __init__(self, controller: ServiceController, config: RagitConfig) -> None:
        self.controller: ServiceController = controller
        self.config: RagitConfig = config
        self.logger = get_service_logger("orchestrator")

    def start_all(self) -> bool:
        """모든 서비스 시작"""
        self.logger.info("🚀 Starting RAGIT system...")

        # 시작 순서: backend -> gateway -> rag_worker -> frontend
        start_order = ['backend', 'gateway', 'rag_worker', 'frontend']

        for service_name in start_order:
            if not self.controller.start_service(service_name):
                self.logger.error(f"Failed to start {service_name}, stopping all services")
                self.stop_all()
                return False
            time.sleep(2)  # 각 서비스 간 시작 간격

        self.logger.info("✅ All services started successfully!")
        return True

    def stop_all(self) -> bool:
        """모든 서비스 종료"""
        self.logger.info("🛑 Stopping all services...")

        # 종료 순서: frontend -> rag_worker -> gateway -> backend
        stop_order = ['frontend', 'rag_worker', 'gateway', 'backend']

        success = True
        for service_name in stop_order:
            if self.controller.is_service_running(service_name):
                if not self.controller.stop_service(service_name):
                    success = False
                time.sleep(1)

        if success:
            self.logger.info("✅ All services stopped successfully!")
        else:
            self.logger.warning("⚠️ Some services failed to stop properly")

        return success

    def restart_all(self) -> bool:
        """모든 서비스 재시작"""
        self.logger.info("🔄 Restarting all services...")

        if self.stop_all():
            time.sleep(3)
            return self.start_all()
        return False

    def start_dev_mode(self) -> bool:
        """개발 모드로 시작 (로그 출력 증가)"""
        self.logger.info("🛠️ Starting in development mode...")
        return self.start_all()

    def show_status(self) -> None:
        """현재 실행 중인 서비스 상태 표시"""
        self.logger.info("📊 Service Status:")

        for service_name in self.config.get_all_services():
            if self.controller.is_service_running(service_name):
                port = self.controller._get_service_port(service_name)
                memory = self.controller.get_service_memory_usage(service_name)
                pid = self.controller.get_service_pid(service_name)

                status_info = f"✅ {service_name.upper():<12} RUNNING"
                if port:
                    status_info += f" (port: {port})"
                if memory:
                    status_info += f" (memory: {memory:.1f}MB)"
                if pid:
                    status_info += f" (pid: {pid})"

                self.logger.info(status_info)
            else:
                self.logger.info(f"❌ {service_name.upper():<12} STOPPED")

    def show_service_info(self) -> None:
        """서비스 접속 정보 표시"""
        self.logger.info("🌐 Service URLs:")
        self.logger.info(f"   Frontend:  http://localhost:{self.config.frontend_port}")
        self.logger.info(f"   Backend:   http://localhost:{self.config.backend_port}")
        self.logger.info(f"   Gateway:   http://localhost:{self.config.gateway_port}")

    def monitor_services(self) -> None:
        """서비스 모니터링 모드"""
        self.logger.info("👀 Starting service monitoring (Ctrl+C to stop)")

        try:
            while True:
                self.show_status()
                time.sleep(10)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped")


class SignalHandler:
    """시그널 처리 클래스"""

    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self.orchestrator: SystemOrchestrator = orchestrator
        self.logger = get_service_logger("signal")
        self.setup_signal_handlers()

    def setup_signal_handlers(self) -> None:
        """프로세스 종료 시그널 핸들러 설정"""
        def signal_handler(signum: int, frame: Any) -> None:
            self.logger.info("Received termination signal, stopping all services...")
            self.orchestrator.stop_all()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)


class ProcessManager:
    """메인 프로세스 매니저 - 의존성 조립 및 파사드 역할"""

    def __init__(self, config: Optional[RagitConfig] = None) -> None:
        self.config = config or RagitConfig()

        # 의존성 조립
        self.monitor = ProcessMonitor()
        self.controller = ServiceController(self.config, self.monitor)
        self.orchestrator = SystemOrchestrator(self.controller, self.config)
        self.signal_handler = SignalHandler(self.orchestrator)

        self.logger = get_service_logger("manager")

    def start_service(self, service_name: str) -> bool:
        """개별 서비스 시작"""
        return self.controller.start_service(service_name)

    def stop_service(self, service_name: str) -> bool:
        """개별 서비스 종료"""
        return self.controller.stop_service(service_name)

    def restart_service(self, service_name: str) -> bool:
        """개별 서비스 재시작"""
        return self.controller.restart_service(service_name)

    def start_all(self) -> bool:
        """모든 서비스 시작"""
        return self.orchestrator.start_all()

    def stop_all(self) -> bool:
        """모든 서비스 종료"""
        return self.orchestrator.stop_all()

    def restart_all(self) -> bool:
        """모든 서비스 재시작"""
        return self.orchestrator.restart_all()

    def start_dev_mode(self) -> bool:
        """개발 모드로 시작"""
        return self.orchestrator.start_dev_mode()

    def show_status(self) -> None:
        """서비스 상태 표시"""
        self.orchestrator.show_status()

    def show_service_info(self) -> None:
        """서비스 정보 표시"""
        self.orchestrator.show_service_info()

    def monitor_services(self) -> None:
        """서비스 모니터링"""
        self.orchestrator.monitor_services()

    def is_service_running(self, service_name: str) -> bool:
        """서비스 실행 상태 확인"""
        return self.controller.is_service_running(service_name)


def main() -> None:
    """Process Manager CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description='RAGIT Process Manager')
    parser.add_argument('action', nargs='?', choices=[
        'start-all', 'stop-all', 'restart-all', 'status', 'monitor', 'dev',
        'start-backend', 'start-frontend', 'start-gateway', 'start-rag-worker',
        'stop-backend', 'stop-frontend', 'stop-gateway', 'stop-rag-worker',
        'restart-backend', 'restart-frontend', 'restart-gateway', 'restart-rag-worker'
    ], default='start-all', help='실행할 액션')

    args = parser.parse_args()
    manager = ProcessManager()

    try:
        if args.action == 'start-all':
            if manager.start_all():
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    manager.stop_all()
            else:
                sys.exit(1)

        elif args.action == 'stop-all':
            manager.stop_all()

        elif args.action == 'restart-all':
            if not manager.restart_all():
                sys.exit(1)

        elif args.action == 'status':
            manager.show_status()

        elif args.action == 'monitor':
            manager.monitor_services()

        elif args.action == 'dev':
            if manager.start_dev_mode():
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    manager.stop_all()
            else:
                sys.exit(1)

        elif args.action.startswith('start-'):
            service = args.action.replace('start-', '').replace('-', '_')
            if not manager.start_service(service):
                sys.exit(1)

        elif args.action.startswith('stop-'):
            service = args.action.replace('stop-', '').replace('-', '_')
            if not manager.stop_service(service):
                sys.exit(1)

        elif args.action.startswith('restart-'):
            service = args.action.replace('restart-', '').replace('-', '_')
            if not manager.restart_service(service):
                sys.exit(1)

    except KeyboardInterrupt:
        manager.logger.info("Received interrupt signal, stopping all services...")
        manager.stop_all()


if __name__ == "__main__":
    main()