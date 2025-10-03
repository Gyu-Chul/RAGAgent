#!/usr/bin/env python3
"""
RAGIT Docker Manager SDK
Docker 컨테이너 관리를 위한 유틸리티 클래스
"""

import subprocess
import sys
import os
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from .config import RagitConfig
from .logger import get_service_logger


class DockerManager:
    """Docker 컨테이너 관리 클래스"""

    def __init__(self, config: Optional[RagitConfig] = None) -> None:
        self.config = config or RagitConfig()
        self.logger = get_service_logger("docker")
        self.project_name: str = "ragit"

    def _run_command(self, command: List[str], capture_output: bool = True, cwd: Optional[Path] = None) -> Optional[str]:
        """명령어 실행"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=cwd or self.config.work_dir,
                    encoding='utf-8',
                    errors='replace'
                )
                return result.stdout.strip()
            else:
                subprocess.run(
                    command,
                    check=True,
                    cwd=cwd or self.config.work_dir,
                    encoding='utf-8',
                    errors='replace'
                )
                return ""
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            if capture_output and e.stderr:
                self.logger.error(f"Error: {e.stderr}")
            return None

    def _check_docker(self) -> bool:
        """Docker 환경 확인"""
        # Docker 버전 확인
        if not self._run_command(["docker", "--version"]):
            self.logger.error("Docker is not installed")
            return False

        # Docker 데몬 실행 확인
        if not self._run_command(["docker", "info"]):
            self.logger.error("Docker daemon is not running")
            return False

        # Docker Compose 확인
        if not (self._run_command(["docker-compose", "--version"]) or
                self._run_command(["docker", "compose", "version"])):
            self.logger.error("Docker Compose is not installed")
            return False

        return True

    def _get_compose_command(self) -> List[str]:
        """Docker Compose 명령어 반환"""
        if self._run_command(["docker", "compose", "version"]):
            return ["docker", "compose"]
        else:
            return ["docker-compose"]

    def _get_compose_file(self, mode: str = "dev") -> str:
        """모드에 따른 Compose 파일 반환"""
        return self.config.get_docker_compose_file(mode)

    def build(self, mode: str = "dev") -> bool:
        """Docker 이미지 빌드"""
        if not self._check_docker():
            return False

        compose_file = self._get_compose_file(mode)
        self.logger.info(f"🔨 Building Docker images (mode: {mode})")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "build", "--no-cache"]

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info("✅ Docker images built successfully")
            return True

        self.logger.error("❌ Docker image build failed")
        return False

    def start(self, mode: str = "dev") -> bool:
        """Docker 컨테이너 시작"""
        if not self._check_docker():
            return False

        compose_file = self._get_compose_file(mode)
        self.logger.info(f"🐳 Starting Docker containers (mode: {mode})")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "up", "-d"]

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info("✅ Docker containers started successfully")
            self._show_status(mode)
            return True

        self.logger.error("❌ Docker container start failed")
        return False

    def start_local_infrastructure(self) -> bool:
        """로컬 인프라 컨테이너 시작 (PostgreSQL, Redis)"""
        if not self._check_docker():
            return False

        compose_file = "docker-compose.local.yml"
        self.logger.info("🐳 Starting local infrastructure (PostgreSQL, Redis)")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "up", "-d"]

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info("✅ Local infrastructure started successfully")
            self._wait_for_services_healthy(compose_file)
            return True

        self.logger.error("❌ Local infrastructure start failed")
        return False

    def stop_local_infrastructure(self) -> bool:
        """로컬 인프라 컨테이너 중지"""
        if not self._check_docker():
            return False

        compose_file = "docker-compose.local.yml"
        self.logger.info("🛑 Stopping local infrastructure")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "down"]

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info("✅ Local infrastructure stopped successfully")
            return True

        self.logger.error("❌ Local infrastructure stop failed")
        return False

    def _wait_for_services_healthy(self, compose_file: str, timeout: int = 30) -> bool:
        """서비스가 healthy 상태가 될 때까지 대기"""
        import time

        self.logger.info("⏳ Waiting for services to be healthy...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # docker ps를 사용하여 직접 컨테이너 상태 확인
                ps_command = ["docker", "ps", "--filter", "name=ragit-", "--format", "{{.Names}}\t{{.Status}}"]
                output = self._run_command(ps_command)

                if output:
                    lines = output.strip().split('\n')
                    containers = {}

                    for line in lines:
                        if '\t' in line:
                            name, status = line.split('\t', 1)
                            containers[name] = status

                    # PostgreSQL과 Redis 컨테이너가 모두 실행 중인지 확인
                    postgres_running = any('postgres' in name and 'Up' in status
                                          for name, status in containers.items())
                    redis_running = any('redis' in name and 'Up' in status
                                       for name, status in containers.items())

                    if postgres_running and redis_running:
                        # 추가로 헬스체크 완료 확인 (healthy 상태)
                        all_healthy = True
                        for name, status in containers.items():
                            if 'health' in status.lower():
                                if 'healthy' not in status.lower():
                                    all_healthy = False
                                    break

                        if all_healthy:
                            self.logger.info("✅ All services are healthy")
                            return True

            except Exception as e:
                self.logger.debug(f"Health check error (will retry): {e}")

            time.sleep(2)

        self.logger.warning("⚠️  Timeout waiting for services to be healthy")
        return False

    def stop(self, mode: str = "dev") -> bool:
        """Docker 컨테이너 중지"""
        if not self._check_docker():
            return False

        compose_file = self._get_compose_file(mode)
        self.logger.info(f"🛑 Stopping Docker containers (mode: {mode})")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "down"]

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info("✅ Docker containers stopped successfully")
            return True

        self.logger.error("❌ Docker container stop failed")
        return False

    def restart(self, mode: str = "dev") -> bool:
        """Docker 컨테이너 재시작"""
        self.logger.info(f"🔄 Restarting Docker containers (mode: {mode})")

        if self.stop(mode) and self.start(mode):
            self.logger.info("✅ Docker containers restarted successfully")
            return True

        self.logger.error("❌ Docker container restart failed")
        return False

    def logs(self, service: Optional[str] = None, follow: bool = True, mode: str = "dev") -> bool:
        """Docker 컨테이너 로그 확인"""
        if not self._check_docker():
            return False

        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "logs"]

        if follow:
            command.append("-f")

        if service:
            command.append(service)

        log_type = "(live)" if follow else "(static)"
        service_info = f" for {service}" if service else ""
        self.logger.info(f"📋 Viewing Docker logs{service_info} {log_type}")

        if self._run_command(command, capture_output=False) is not None:
            return True

        self.logger.error("❌ Failed to view Docker logs")
        return False

    def _show_status(self, mode: str = "dev") -> None:
        """서비스 상태 표시"""
        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", compose_file, "ps"]

        output = self._run_command(command)
        if output:
            self.logger.info("🎯 Container Status:")
            for line in output.split('\n'):
                if line.strip():
                    self.logger.info(f"   {line}")

            self.logger.info("🌐 Service URLs:")
            self.logger.info(f"   Frontend:  http://localhost:{self.config.frontend_port}")
            self.logger.info(f"   Backend:   http://localhost:{self.config.backend_port}")
            self.logger.info(f"   Gateway:   http://localhost:{self.config.gateway_port}")

    def status(self, mode: str = "dev") -> bool:
        """현재 상태 확인"""
        if not self._check_docker():
            return False

        self._show_status(mode)
        return True

    def cleanup(self) -> bool:
        """사용하지 않는 Docker 리소스 정리"""
        if not self._check_docker():
            return False

        self.logger.info("🧹 Cleaning up Docker resources...")

        commands = [
            ["docker", "system", "prune", "-f"],
            ["docker", "volume", "prune", "-f"],
            ["docker", "network", "prune", "-f"]
        ]

        success = True
        for command in commands:
            if self._run_command(command, capture_output=False) is None:
                success = False

        if success:
            self.logger.info("✅ Docker resources cleaned up successfully")
        else:
            self.logger.error("❌ Docker cleanup failed")

        return success

    def get_container_stats(self, mode: str = "dev") -> Optional[Dict[str, Any]]:
        """컨테이너 리소스 사용량 확인"""
        if not self._check_docker():
            return None

        try:
            # Docker stats를 JSON 형태로 한 번만 실행
            result = self._run_command([
                "docker", "stats", "--no-stream", "--format",
                "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
            ])

            if result:
                self.logger.info("📊 Container Resource Usage:")
                for line in result.split('\n'):
                    if line.strip():
                        self.logger.info(f"   {line}")
                return {"stats": result}

        except Exception as e:
            self.logger.error(f"Failed to get container stats: {e}")

        return None

    def exec_command(self, service: str, command: List[str], mode: str = "dev") -> Optional[str]:
        """컨테이너 내부에서 명령어 실행"""
        if not self._check_docker():
            return None

        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()

        exec_command = compose_cmd + ["-f", compose_file, "exec", service] + command

        self.logger.info(f"🔧 Executing command in {service}: {' '.join(command)}")

        return self._run_command(exec_command)

    def get_service_logs(self, service: str, lines: int = 100, mode: str = "dev") -> Optional[str]:
        """특정 서비스의 로그 반환"""
        if not self._check_docker():
            return None

        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()

        command = compose_cmd + ["-f", compose_file, "logs", "--tail", str(lines), service]

        return self._run_command(command)

    def scale_service(self, service: str, replicas: int, mode: str = "dev") -> bool:
        """서비스 스케일링 (프로덕션 모드에서만 유효)"""
        if mode != "prod":
            self.logger.warning("Service scaling is only available in production mode")
            return False

        if not self._check_docker():
            return False

        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()

        command = compose_cmd + ["-f", compose_file, "up", "-d", "--scale", f"{service}={replicas}"]

        self.logger.info(f"📈 Scaling {service} to {replicas} replicas")

        if self._run_command(command, capture_output=False) is not None:
            self.logger.info(f"✅ Successfully scaled {service} to {replicas} replicas")
            return True

        self.logger.error(f"❌ Failed to scale {service}")
        return False

    def health_check(self, mode: str = "dev") -> Dict[str, bool]:
        """모든 서비스의 헬스체크 실행"""
        if not self._check_docker():
            return {}

        compose_file = self._get_compose_file(mode)
        compose_cmd = self._get_compose_command()

        # 실행 중인 컨테이너 목록 가져오기
        ps_command = compose_cmd + ["-f", compose_file, "ps", "--services", "--filter", "status=running"]
        running_services = self._run_command(ps_command)

        if not running_services:
            return {}

        health_status = {}
        for service in running_services.split('\n'):
            if service.strip():
                # 각 서비스의 헬스체크 상태 확인
                inspect_command = ["docker", "inspect", "--format", "{{.State.Health.Status}}", f"{self.project_name}_{service}_1"]
                health = self._run_command(inspect_command)
                health_status[service] = health == "healthy" if health else False

        return health_status


def main() -> None:
    """Docker Manager CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description='RAGIT Docker Manager')
    parser.add_argument('action', choices=[
        'build', 'start', 'stop', 'restart', 'logs', 'status', 'cleanup'
    ], help='Docker 관리 액션')
    parser.add_argument('--mode', choices=['dev', 'prod'], default='dev',
                       help='실행 모드 (기본값: dev)')
    parser.add_argument('--service', help='특정 서비스 (logs 액션용)')
    parser.add_argument('--no-follow', action='store_true',
                       help='로그 실시간 추적 비활성화')

    args = parser.parse_args()
    manager = DockerManager()

    if args.action == 'build':
        success = manager.build(args.mode)
    elif args.action == 'start':
        success = manager.start(args.mode)
    elif args.action == 'stop':
        success = manager.stop(args.mode)
    elif args.action == 'restart':
        success = manager.restart(args.mode)
    elif args.action == 'logs':
        success = manager.logs(args.service, not args.no_follow, args.mode)
    elif args.action == 'status':
        success = manager.status(args.mode)
    elif args.action == 'cleanup':
        success = manager.cleanup()
    else:
        success = False

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()