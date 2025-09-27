"""
RAGIT SDK 유틸리티 함수들
공통으로 사용되는 헬퍼 함수 및 유틸리티
"""

import os
import sys
import time
import socket
import psutil
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

from .logger import get_service_logger


def check_port_available(port: int, host: str = "localhost") -> bool:
    """포트 사용 가능 여부 확인"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # 연결 실패 = 포트 사용 가능
    except Exception:
        return False


def wait_for_service(url: str, timeout: int = 30, interval: int = 1) -> bool:
    """서비스가 응답할 때까지 대기"""
    logger = get_service_logger("utils")
    logger.info(f"Waiting for service at {url}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Service is ready at {url}")
                return True
        except requests.RequestException:
            pass

        time.sleep(interval)

    logger.warning(f"⚠️ Service at {url} is not ready after {timeout}s")
    return False


def check_service_health(url: str) -> Dict[str, Any]:
    """서비스 헬스체크 실행"""
    try:
        start_time = time.time()
        response = requests.get(f"{url}/health", timeout=10)
        response_time = (time.time() - start_time) * 1000  # ms

        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "details": response.json() if response.status_code == 200 else None
        }
    except requests.RequestException as e:
        return {
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": None,
            "error": str(e)
        }


def get_system_info() -> Dict[str, Any]:
    """시스템 정보 반환"""
    try:
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "python_version": sys.version,
            "platform": sys.platform
        }
    except Exception as e:
        return {"error": str(e)}


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    """사용 가능한 포트 찾기"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    return None


def kill_process_on_port(port: int) -> bool:
    """특정 포트를 사용하는 프로세스 종료"""
    logger = get_service_logger("utils")

    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections'] or []
                for conn in connections:
                    if conn.laddr.port == port:
                        logger.warning(f"Killing process {proc.info['pid']} ({proc.info['name']}) using port {port}")
                        proc.terminate()
                        proc.wait(timeout=5)
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Failed to kill process on port {port}: {e}")
        return False

    return False


def ensure_directory(path: Path) -> bool:
    """디렉토리 생성 보장"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger = get_service_logger("utils")
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def read_file_safe(file_path: Path) -> Optional[str]:
    """안전한 파일 읽기"""
    try:
        return file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger = get_service_logger("utils")
        logger.error(f"Failed to read file {file_path}: {e}")
        return None


def write_file_safe(file_path: Path, content: str) -> bool:
    """안전한 파일 쓰기"""
    try:
        ensure_directory(file_path.parent)
        file_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        logger = get_service_logger("utils")
        logger.error(f"Failed to write file {file_path}: {e}")
        return False


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """프로세스 정보 반환"""
    try:
        proc = psutil.Process(pid)
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "status": proc.status(),
            "cpu_percent": proc.cpu_percent(),
            "memory_info": proc.memory_info()._asdict(),
            "create_time": proc.create_time(),
            "cmdline": proc.cmdline()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def format_bytes(bytes_value: int) -> str:
    """바이트를 사람이 읽기 쉬운 형태로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """초를 사람이 읽기 쉬운 형태로 변환"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_git_info() -> Dict[str, Optional[str]]:
    """Git 정보 반환"""
    try:
        import subprocess

        def run_git_command(cmd: List[str]) -> Optional[str]:
            try:
                result = subprocess.run(
                    ['git'] + cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                return None

        return {
            "branch": run_git_command(['rev-parse', '--abbrev-ref', 'HEAD']),
            "commit": run_git_command(['rev-parse', 'HEAD']),
            "short_commit": run_git_command(['rev-parse', '--short', 'HEAD']),
            "dirty": "dirty" if run_git_command(['status', '--porcelain']) else "clean"
        }
    except Exception:
        return {
            "branch": None,
            "commit": None,
            "short_commit": None,
            "dirty": None
        }


def create_backup(source_path: Path, backup_dir: Path) -> Optional[Path]:
    """파일 또는 디렉토리 백업 생성"""
    try:
        import shutil
        from datetime import datetime

        ensure_directory(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}_{timestamp}"
        backup_path = backup_dir / backup_name

        if source_path.is_file():
            shutil.copy2(source_path, backup_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, backup_path)
        else:
            return None

        return backup_path
    except Exception as e:
        logger = get_service_logger("utils")
        logger.error(f"Failed to create backup: {e}")
        return None


def cleanup_old_files(directory: Path, max_age_days: int = 7, pattern: str = "*") -> int:
    """오래된 파일 정리"""
    try:
        import glob
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    removed_count += 1

        return removed_count
    except Exception as e:
        logger = get_service_logger("utils")
        logger.error(f"Failed to cleanup old files: {e}")
        return 0