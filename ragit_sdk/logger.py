"""
RAGIT 로깅 설정
통합 로깅 시스템 설정 및 관리
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import colorama
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """색상이 있는 로그 포맷터"""

    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        # 색상 적용
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"

        # 서비스 이름 색상 적용
        if hasattr(record, 'service'):
            record.service = f"{Fore.BLUE}[{record.service}]{Style.RESET_ALL}"

        return super().format(record)


def setup_logger(
    name: str = "ragit",
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """RAGIT 로거 설정"""

    # colorama 초기화 (Windows 호환성)
    colorama.init()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 포맷터 설정
    console_format = "%(asctime)s - %(service)-10s - %(levelname)-8s - %(message)s"
    file_format = "%(asctime)s - %(name)s - %(service)s - %(levelname)s - %(message)s"

    # 콘솔 핸들러
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(console_format, datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 파일 핸들러
    if log_dir:
        log_dir.mkdir(exist_ok=True)

        # 전체 로그 파일
        log_file = log_dir / f"ragit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 에러 로그 파일
        error_file = log_dir / f"ragit_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

    return logger


def get_service_logger(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """서비스별 로거 생성"""
    logger = logging.getLogger(f"ragit.{service_name}")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 서비스 이름을 로그 레코드에 추가하는 어댑터
    logger = ServiceLoggerAdapter(logger, {"service": service_name})

    return logger


class ServiceLoggerAdapter(logging.LoggerAdapter):
    """서비스 이름을 포함하는 로그 어댑터"""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        return msg, {**kwargs, "extra": self.extra}


def log_service_start(service_name: str, port: Optional[int] = None) -> None:
    """서비스 시작 로그"""
    logger = get_service_logger("manager")
    port_info = f" on port {port}" if port else ""
    logger.info(f"🚀 Starting {service_name}{port_info}")


def log_service_stop(service_name: str) -> None:
    """서비스 중지 로그"""
    logger = get_service_logger("manager")
    logger.info(f"🛑 Stopping {service_name}")


def log_service_error(service_name: str, error: str) -> None:
    """서비스 에러 로그"""
    logger = get_service_logger("manager")
    logger.error(f"❌ {service_name} error: {error}")


def log_service_ready(service_name: str, url: Optional[str] = None) -> None:
    """서비스 준비 완료 로그"""
    logger = get_service_logger("manager")
    url_info = f" at {url}" if url else ""
    logger.info(f"✅ {service_name} is ready{url_info}")


# 전역 로거 인스턴스
_global_logger: Optional[logging.Logger] = None


def get_global_logger() -> logging.Logger:
    """전역 로거 반환"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    return _global_logger