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

from ..config import RagitConfig
from ..logger import get_service_logger, log_service_start, log_service_stop, log_service_error, log_service_ready


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
        log_service_stop(service_name)

        # 메모리상의 프로세스가 있으면 그것을 종료
        if service_name in self.processes:
            process = self.processes[service_name]
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

        # 메모리에 없으면 포트 기반으로 프로세스 찾아서 종료
        return self._stop_service_by_port(service_name)

    def _stop_service_by_port(self, service_name: str) -> bool:
        """포트 기반으로 서비스 프로세스 찾아서 종료"""
        port_map = {
            'backend': self.config.backend_port,
            'frontend': self.config.frontend_port,
            'gateway': self.config.gateway_port,
            'rag_worker': None
        }

        port = port_map.get(service_name)
        if port is None:
            # rag_worker의 경우 celery 프로세스를 찾아서 종료
            if service_name == 'rag_worker':
                return self._stop_celery_processes()
            return True

        try:
            import psutil

            # 포트를 사용하는 프로세스 찾기
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.connections(kind='inet')
                    for conn in connections:
                        if (conn.laddr.port == port and
                            conn.status == psutil.CONN_LISTEN):
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                                self.logger.info(f"✅ {service_name} terminated gracefully")
                            except psutil.TimeoutExpired:
                                proc.kill()
                                self.logger.warning(f"⚠️ {service_name} force killed")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            self.logger.warning(f"{service_name} process not found on port {port}")
            return True

        except ImportError:
            # psutil이 없으면 netstat으로 PID 찾기
            return self._stop_service_by_netstat(service_name, port)

    def _stop_celery_processes(self) -> bool:
        """Celery 프로세스 종료"""
        try:
            import psutil

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline_list = proc.info['cmdline']
                    if cmdline_list is None:
                        continue
                    cmdline = ' '.join(cmdline_list)
                    if 'celery' in cmdline and 'rag_worker' in cmdline:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                            self.logger.info(f"✅ rag_worker terminated gracefully")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            self.logger.warning(f"⚠️ rag_worker force killed")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                    continue

            return True
        except ImportError:
            self.logger.warning("psutil not available, cannot stop rag_worker")
            return True

    def _stop_service_by_netstat(self, service_name: str, port: int) -> bool:
        """netstat을 사용해서 프로세스 종료 (Windows)"""
        try:
            import subprocess
            import os

            # netstat으로 포트 사용 프로세스 찾기
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                shell=True
            )

            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            # 프로세스 종료
                            subprocess.run(['taskkill', '/PID', pid, '/F'],
                                         shell=True, capture_output=True)
                            self.logger.info(f"✅ {service_name} (PID: {pid}) terminated")
                            return True
                        except Exception as e:
                            self.logger.error(f"Failed to kill PID {pid}: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Error stopping {service_name} by netstat: {e}")
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
        # 먼저 메모리상의 프로세스 확인
        if (service_name in self.processes and
                self.processes[service_name].poll() is None):
            return True

        # 메모리에 없으면 포트 기반으로 확인
        import socket

        port_map = {
            'backend': self.config.backend_port,
            'frontend': self.config.frontend_port,
            'gateway': self.config.gateway_port,
            'rag_worker': None  # rag_worker는 포트를 사용하지 않음
        }

        port = port_map.get(service_name)
        if port is None:
            # rag_worker의 경우 celery 프로세스 확인
            if service_name == 'rag_worker':
                return self._is_celery_running()
            return False

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False

    def _is_celery_running(self) -> bool:
        """Celery 프로세스 실행 상태 확인"""
        try:
            import psutil

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline_list = proc.info['cmdline']
                    if cmdline_list is None:
                        continue
                    cmdline = ' '.join(cmdline_list)
                    if ('celery' in cmdline and 'rag_worker' in cmdline and
                        'worker' in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                    continue

            return False
        except ImportError:
            # psutil이 없으면 tasklist로 확인 (Windows)
            return self._is_celery_running_by_tasklist()

    def _is_celery_running_by_tasklist(self) -> bool:
        """tasklist를 사용해서 celery 프로세스 확인 (Windows)"""
        try:
            import subprocess

            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                shell=True
            )

            # python.exe 프로세스들 중에서 celery와 rag_worker가 포함된 것 찾기
            if 'python.exe' in result.stdout:
                # 좀 더 정확한 확인을 위해 wmic 사용
                wmic_result = subprocess.run(
                    ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'CommandLine', '/format:csv'],
                    capture_output=True,
                    text=True,
                    shell=True
                )

                for line in wmic_result.stdout.splitlines():
                    if 'celery' in line and 'rag_worker' in line and 'worker' in line:
                        return True

            return False
        except Exception:
            return False

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

        # 1. Docker 인프라 시작 (PostgreSQL, Redis)
        from .docker_manager import DockerManager
        docker_manager = DockerManager(self.config)

        if not docker_manager.start_local_infrastructure():
            self.logger.error("Failed to start Docker infrastructure")
            return False

        # 인프라가 준비될 때까지 잠시 대기
        time.sleep(3)

        # 2. 서비스 시작 순서: backend -> gateway -> rag_worker -> frontend
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

        # 1. 서비스 종료 순서: frontend -> rag_worker -> gateway -> backend
        stop_order = ['frontend', 'rag_worker', 'gateway', 'backend']

        success = True
        for service_name in stop_order:
            if self.controller.is_service_running(service_name):
                if not self.controller.stop_service(service_name):
                    success = False
                time.sleep(1)

        # 2. Docker 인프라 종료 (PostgreSQL, Redis)
        from .docker_manager import DockerManager
        docker_manager = DockerManager(self.config)

        if not docker_manager.stop_local_infrastructure():
            self.logger.warning("⚠️  Failed to stop Docker infrastructure")
            success = False

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

        # 1. Docker 인프라 상태 확인
        from .docker_manager import DockerManager
        docker_manager = DockerManager(self.config)

        self.logger.info("\n🐳 Docker Infrastructure:")
        docker_status = self._check_docker_infrastructure_status(docker_manager)

        for container_name, status in docker_status.items():
            if status['running']:
                status_info = f"✅ {container_name.upper():<12} RUNNING"
                if status.get('port'):
                    status_info += f" (port: {status['port']})"
                if status.get('health'):
                    status_info += f" [{status['health']}]"
                self.logger.info(status_info)
            else:
                self.logger.info(f"❌ {container_name.upper():<12} STOPPED")

        # 2. RAGIT 서비스 상태 확인
        self.logger.info("\n🚀 RAGIT Services:")

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

    def _check_docker_infrastructure_status(self, docker_manager: Any) -> Dict[str, Dict[str, Any]]:
        """Docker 인프라 상태 확인"""
        import subprocess

        status = {
            'postgresql': {'running': False, 'port': 5432, 'health': None},
            'redis': {'running': False, 'port': 6379, 'health': None}
        }

        try:
            # docker ps로 컨테이너 상태 확인
            ps_command = ["docker", "ps", "--filter", "name=ragit-", "--format", "{{.Names}}\t{{.Status}}"]
            result = subprocess.run(
                ps_command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')

                for line in lines:
                    if '\t' in line:
                        name, container_status = line.split('\t', 1)

                        # PostgreSQL 확인
                        if 'postgres' in name.lower():
                            status['postgresql']['running'] = 'Up' in container_status
                            if 'healthy' in container_status.lower():
                                status['postgresql']['health'] = 'healthy'
                            elif 'unhealthy' in container_status.lower():
                                status['postgresql']['health'] = 'unhealthy'
                            elif 'health' in container_status.lower():
                                status['postgresql']['health'] = 'starting'

                        # Redis 확인
                        if 'redis' in name.lower():
                            status['redis']['running'] = 'Up' in container_status
                            if 'healthy' in container_status.lower():
                                status['redis']['health'] = 'healthy'
                            elif 'unhealthy' in container_status.lower():
                                status['redis']['health'] = 'unhealthy'
                            elif 'health' in container_status.lower():
                                status['redis']['health'] = 'starting'

        except Exception as e:
            self.logger.debug(f"Error checking Docker infrastructure: {e}")

        return status

    def show_service_info(self) -> None:
        """서비스 접속 정보 표시"""
        self.logger.info("🌐 Service URLs:")
        self.logger.info(f"   Frontend:  http://localhost:{self.config.frontend_port}")
        self.logger.info(f"   Backend:   http://localhost:{self.config.backend_port}")
        self.logger.info(f"   Gateway:   http://localhost:{self.config.gateway_port}")

    def monitor_services(self) -> None:
        """서비스 모니터링 모드 - 날짜별 로그 파일 실시간 모니터링"""
        self.logger.info("👀 Starting service monitoring (Ctrl+C to stop)")
        self.logger.info("📋 Real-time log monitoring and health check...")

        import threading
        import socket
        import time
        from pathlib import Path
        from datetime import datetime

        stop_monitoring = threading.Event()
        log_base_dir = Path("logs")
        today = datetime.now().strftime("%Y-%m-%d")
        today_log_dir = log_base_dir / today

        def find_latest_log_file(service_name: str) -> Optional[Path]:
            """서비스의 최신 로그 파일 찾기"""
            if not today_log_dir.exists():
                return None

            # 오늘 날짜의 해당 서비스 로그 파일들 중 가장 최신 것 찾기
            pattern = f"{service_name}_*.log"
            log_files = list(today_log_dir.glob(pattern))

            if not log_files:
                return None

            # 파일 수정 시간 기준으로 정렬하여 가장 최신 파일 반환
            return max(log_files, key=lambda f: f.stat().st_mtime)

        def tail_log_file(service_name: str, log_file: Path) -> None:
            """로그 파일을 실시간으로 tail"""
            if not log_file.exists():
                self.logger.warning(f"Log file not found: {log_file}")
                return

            try:
                # 파일 끝으로 이동
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)  # 파일 끝으로 이동

                    while not stop_monitoring.is_set():
                        line = f.readline()
                        if line:
                            # 로그 라인에서 타임스탬프와 서비스명이 이미 포함되어 있으므로 그대로 출력
                            print(line.strip())
                        else:
                            time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error tailing {service_name} log: {e}")

        # 로그 파일 tailing 스레드들
        log_threads = []
        service_names = ['backend', 'frontend', 'gateway', 'rag_worker']

        # 각 서비스별 최신 로그 파일 찾아서 모니터링 시작
        for service_name in service_names:
            if self.controller.is_service_running(service_name):
                log_file = find_latest_log_file(service_name)
                if log_file:
                    self.logger.info(f"📄 Monitoring {service_name} log: {log_file}")
                    thread = threading.Thread(
                        target=tail_log_file,
                        args=(service_name, log_file),
                        daemon=True
                    )
                    thread.start()
                    log_threads.append((service_name, thread))
                else:
                    self.logger.warning(f"⚠️  No log file found for {service_name}")
            else:
                self.logger.warning(f"⛔ Service {service_name} is not running")

        def check_service_health(service_name: str) -> dict:
            """서비스 헬스체크"""
            result = {
                'name': service_name,
                'running': self.controller.is_service_running(service_name),
                'port_open': False,
                'response_time': None,
                'error': None
            }

            if service_name == 'rag_worker':
                # rag_worker는 포트 기반 체크가 아님
                return result

            port_map = {
                'backend': self.config.backend_port,
                'frontend': self.config.frontend_port,
                'gateway': self.config.gateway_port
            }

            port = port_map.get(service_name)
            if port and result['running']:
                try:
                    start_time = time.time()
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(3)
                        result_code = sock.connect_ex(('localhost', port))
                        result['port_open'] = (result_code == 0)
                        result['response_time'] = round((time.time() - start_time) * 1000, 2)
                except Exception as e:
                    result['error'] = str(e)

            return result

        def show_detailed_status() -> None:
            """상세 상태 표시"""
            self.logger.info("=" * 80)
            self.logger.info("📊 Detailed Service Status:")

            services = ['backend', 'frontend', 'gateway', 'rag_worker']
            health_results = []

            for service_name in services:
                health = check_service_health(service_name)
                health_results.append(health)

                status_icon = "✅" if health['running'] else "❌"
                status_text = "RUNNING" if health['running'] else "STOPPED"

                if service_name == 'rag_worker':
                    self.logger.info(f"   {status_icon} {service_name.upper():<12} {status_text}")
                else:
                    port = getattr(self.config, f"{service_name}_port", "N/A")
                    port_status = "🟢" if health['port_open'] else "🔴" if health['running'] else "⚫"
                    response_info = f" ({health['response_time']}ms)" if health['response_time'] else ""

                    self.logger.info(
                        f"   {status_icon} {service_name.upper():<12} {status_text:<8} "
                        f"Port:{port} {port_status}{response_info}"
                    )

                    if health['error']:
                        self.logger.warning(f"      ⚠️  Connection error: {health['error']}")

            # 전체 시스템 상태 요약
            running_count = sum(1 for h in health_results if h['running'])
            total_count = len(services)

            if running_count == total_count:
                system_status = "🟢 All Systems Operational"
            elif running_count > 0:
                system_status = f"🟡 Partial System ({running_count}/{total_count} services running)"
            else:
                system_status = "🔴 System Down"

            self.logger.info(f"\n   🔧 System Status: {system_status}")
            self.logger.info(f"   📈 Uptime Check: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 80)

        # 초기 상태 표시
        show_detailed_status()

        # 상태 체크 스레드
        def periodic_health_check() -> None:
            """주기적 헬스체크"""
            check_interval = 30  # 30초마다 체크
            last_check = time.time()

            while not stop_monitoring.is_set():
                current_time = time.time()

                if current_time - last_check >= check_interval:
                    print("\n" + "="*80)
                    print("📊 Health Check Update:")

                    for service_name in ['backend', 'frontend', 'gateway', 'rag_worker']:
                        health = check_service_health(service_name)
                        status_icon = "✅" if health['running'] else "❌"
                        status_text = "RUNNING" if health['running'] else "STOPPED"

                        if service_name == 'rag_worker':
                            print(f"   {status_icon} {service_name.upper():<12} {status_text}")
                        else:
                            port = getattr(self.config, f"{service_name}_port", "N/A")
                            port_status = "🟢" if health['port_open'] else "🔴" if health['running'] else "⚫"
                            response_info = f" ({health['response_time']}ms)" if health['response_time'] else ""
                            print(f"   {status_icon} {service_name.upper():<12} {status_text:<8} Port:{port} {port_status}{response_info}")

                    print("="*80 + "\n")
                    last_check = current_time

                time.sleep(5)

        # 헬스체크 스레드 시작
        health_thread = threading.Thread(target=periodic_health_check, daemon=True)
        health_thread.start()

        self.logger.info("📈 Real-time log streaming started...")
        self.logger.info("💡 Health checks every 30 seconds, logs are streamed in real-time")

        try:
            # 메인 루프 - 로그 모니터링이 스레드에서 실행되므로 단순히 대기
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            stop_monitoring.set()

            # 모든 스레드가 종료될 때까지 잠시 대기
            for service_name, thread in log_threads:
                thread.join(timeout=1)

            health_thread.join(timeout=1)
            print("✅ Monitoring stopped - Services remain running")


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