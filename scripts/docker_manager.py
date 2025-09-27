#!/usr/bin/env python3
"""
Docker 관리 스크립트
RAGIT Docker 컨테이너 관리를 위한 유틸리티
"""

import subprocess
import sys
import os
from typing import List, Optional
import json


class DockerManager:
    """Docker 컨테이너 관리 클래스"""

    def __init__(self) -> None:
        self.compose_file: str = "docker-compose.yml"
        self.project_name: str = "ragit"

    def _run_command(self, command: List[str], capture_output: bool = True) -> Optional[str]:
        """명령어 실행"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            else:
                subprocess.run(command, check=True)
                return None
        except subprocess.CalledProcessError as e:
            print(f"❌ 명령어 실행 실패: {' '.join(command)}")
            if capture_output and e.stderr:
                print(f"오류: {e.stderr}")
            return None

    def _check_docker(self) -> bool:
        """Docker 환경 확인"""
        if not self._run_command(["docker", "--version"]):
            print("❌ Docker가 설치되지 않았습니다.")
            return False

        if not self._run_command(["docker", "info"]):
            print("❌ Docker 데몬이 실행되지 않았습니다.")
            return False

        # Docker Compose 확인
        if not (self._run_command(["docker-compose", "--version"]) or
                self._run_command(["docker", "compose", "version"])):
            print("❌ Docker Compose가 설치되지 않았습니다.")
            return False

        return True

    def _get_compose_command(self) -> List[str]:
        """Docker Compose 명령어 반환"""
        if self._run_command(["docker", "compose", "version"]):
            return ["docker", "compose"]
        else:
            return ["docker-compose"]

    def build(self) -> bool:
        """Docker 이미지 빌드"""
        if not self._check_docker():
            return False

        print("🔨 Docker 이미지 빌드 중...")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", self.compose_file, "build", "--no-cache"]

        if self._run_command(command, capture_output=False) is not None:
            print("✅ Docker 이미지 빌드 완료")
            return True
        return False

    def start(self) -> bool:
        """Docker 컨테이너 시작"""
        if not self._check_docker():
            return False

        print("🐳 Docker 컨테이너 시작 중...")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", self.compose_file, "up", "-d"]

        if self._run_command(command, capture_output=False) is not None:
            print("✅ Docker 컨테이너 시작 완료")
            self._show_status()
            return True
        return False

    def stop(self) -> bool:
        """Docker 컨테이너 중지"""
        if not self._check_docker():
            return False

        print("🛑 Docker 컨테이너 중지 중...")

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", self.compose_file, "down"]

        if self._run_command(command, capture_output=False) is not None:
            print("✅ Docker 컨테이너 중지 완료")
            return True
        return False

    def restart(self) -> bool:
        """Docker 컨테이너 재시작"""
        print("🔄 Docker 컨테이너 재시작 중...")

        if self.stop() and self.start():
            print("✅ Docker 컨테이너 재시작 완료")
            return True
        return False

    def logs(self, service: Optional[str] = None, follow: bool = True) -> bool:
        """Docker 컨테이너 로그 확인"""
        if not self._check_docker():
            return False

        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", self.compose_file, "logs"]

        if follow:
            command.append("-f")

        if service:
            command.append(service)

        print(f"📋 Docker 로그 확인 중{'(실시간)' if follow else ''}...")

        if self._run_command(command, capture_output=False) is not None:
            return True
        return False

    def _show_status(self) -> None:
        """서비스 상태 표시"""
        compose_cmd = self._get_compose_command()
        command = compose_cmd + ["-f", self.compose_file, "ps"]

        output = self._run_command(command)
        if output:
            print("\n🎯 서비스 상태:")
            print(output)

            print("\n🌐 접속 정보:")
            print("- 웹 인터페이스: http://localhost:8000")
            print("- 백엔드 API: http://localhost:8001")
            print("- 게이트웨이: http://localhost:8080")

    def status(self) -> bool:
        """현재 상태 확인"""
        if not self._check_docker():
            return False

        self._show_status()
        return True

    def cleanup(self) -> bool:
        """사용하지 않는 Docker 리소스 정리"""
        if not self._check_docker():
            return False

        print("🧹 Docker 리소스 정리 중...")

        commands = [
            ["docker", "system", "prune", "-f"],
            ["docker", "volume", "prune", "-f"],
            ["docker", "network", "prune", "-f"]
        ]

        for command in commands:
            self._run_command(command, capture_output=False)

        print("✅ Docker 리소스 정리 완료")
        return True


def build() -> None:
    """Docker 이미지 빌드"""
    manager = DockerManager()
    if not manager.build():
        sys.exit(1)


def start() -> None:
    """Docker 컨테이너 시작"""
    manager = DockerManager()
    if not manager.start():
        sys.exit(1)


def stop() -> None:
    """Docker 컨테이너 중지"""
    manager = DockerManager()
    if not manager.stop():
        sys.exit(1)


def restart() -> None:
    """Docker 컨테이너 재시작"""
    manager = DockerManager()
    if not manager.restart():
        sys.exit(1)


def logs() -> None:
    """Docker 컨테이너 로그 확인"""
    manager = DockerManager()
    service = sys.argv[1] if len(sys.argv) > 1 else None
    if not manager.logs(service):
        sys.exit(1)


def status() -> None:
    """Docker 컨테이너 상태 확인"""
    manager = DockerManager()
    if not manager.status():
        sys.exit(1)


def cleanup() -> None:
    """Docker 리소스 정리"""
    manager = DockerManager()
    if not manager.cleanup():
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python docker_manager.py [build|start|stop|restart|logs|status|cleanup]")
        sys.exit(1)

    command = sys.argv[1]
    manager = DockerManager()

    commands = {
        "build": manager.build,
        "start": manager.start,
        "stop": manager.stop,
        "restart": manager.restart,
        "logs": lambda: manager.logs(),
        "status": manager.status,
        "cleanup": manager.cleanup
    }

    if command not in commands:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("사용 가능한 명령어: build, start, stop, restart, logs, status, cleanup")
        sys.exit(1)

    if not commands[command]():
        sys.exit(1)