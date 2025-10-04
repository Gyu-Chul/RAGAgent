"""
레포지토리 파일 스캐너
"""

import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


class FileScanner:
    """레포지토리 내 Python 파일을 스캔하는 클래스"""

    # 제외할 디렉토리 패턴
    EXCLUDE_DIRS: Set[str] = {
        ".git",
        ".github",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "*.egg-info",
    }

    # 제외할 파일 패턴
    EXCLUDE_FILES: Set[str] = {
        "__init__.py",  # 빈 __init__.py는 의미 없음
    }

    def __init__(self, exclude_dirs: Set[str] = None, exclude_files: Set[str] = None) -> None:
        """
        FileScanner 초기화

        Args:
            exclude_dirs: 추가로 제외할 디렉토리 패턴
            exclude_files: 추가로 제외할 파일 패턴
        """
        self.exclude_dirs: Set[str] = self.EXCLUDE_DIRS.copy()
        self.exclude_files: Set[str] = self.EXCLUDE_FILES.copy()

        if exclude_dirs:
            self.exclude_dirs.update(exclude_dirs)
        if exclude_files:
            self.exclude_files.update(exclude_files)

    def should_exclude_dir(self, dir_path: Path) -> bool:
        """
        디렉토리를 제외해야 하는지 확인

        Args:
            dir_path: 확인할 디렉토리 경로

        Returns:
            제외 여부
        """
        dir_name = dir_path.name
        return dir_name in self.exclude_dirs or dir_name.startswith(".")

    def should_exclude_file(self, file_path: Path) -> bool:
        """
        파일을 제외해야 하는지 확인

        Args:
            file_path: 확인할 파일 경로

        Returns:
            제외 여부
        """
        file_name = file_path.name

        # __init__.py는 내용이 있으면 포함
        if file_name == "__init__.py":
            try:
                # 빈 파일이거나 주석만 있으면 제외
                content = file_path.read_text(encoding="utf-8").strip()
                if not content or all(line.startswith("#") for line in content.split("\n") if line.strip()):
                    return True
            except Exception:
                return True

        return file_name in self.exclude_files

    def scan_repository(self, repo_path: Path) -> List[Path]:
        """
        레포지토리 내 모든 Python 파일 스캔

        Args:
            repo_path: 레포지토리 경로

        Returns:
            Python 파일 경로 리스트
        """
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return []

        if not repo_path.is_dir():
            logger.error(f"Repository path is not a directory: {repo_path}")
            return []

        python_files: List[Path] = []

        def scan_dir(directory: Path) -> None:
            """디렉토리를 재귀적으로 스캔"""
            try:
                for item in directory.iterdir():
                    # 디렉토리 처리
                    if item.is_dir():
                        if not self.should_exclude_dir(item):
                            scan_dir(item)
                        continue

                    # 파일 처리
                    if item.is_file() and item.suffix == ".py":
                        if not self.should_exclude_file(item):
                            python_files.append(item)

            except PermissionError:
                logger.warning(f"Permission denied: {directory}")
            except Exception as e:
                logger.error(f"Error scanning directory {directory}: {str(e)}")

        scan_dir(repo_path)

        logger.info(f"Found {len(python_files)} Python files in {repo_path}")
        return sorted(python_files)  # 정렬하여 일관된 순서 유지
