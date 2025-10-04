"""
Git 관련 작업을 처리하는 서비스
"""

import logging
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

from .exceptions import (
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    GitCommandError,
    GitTimeoutError,
)
from .types import CloneResult, StatusResult, PullResult, DeleteResult, CommitInfo

logger = logging.getLogger(__name__)


class GitCommandRunner:
    """Git 명령어 실행을 담당하는 클래스"""

    @staticmethod
    def run(command: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Git 명령어 실행

        Args:
            command: 실행할 명령어 리스트
            cwd: 명령어를 실행할 작업 디렉토리
            timeout: 명령어 타임아웃 (초)

        Returns:
            실행 결과

        Raises:
            GitTimeoutError: 명령어 타임아웃 시
            GitCommandError: 명령어 실행 실패 시
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )

            if result.returncode != 0:
                logger.error(f"Git command failed: {' '.join(command)}")
                logger.error(f"Error: {result.stderr}")
                raise GitCommandError(result.stderr)

            return {"success": True, "stdout": result.stdout, "stderr": result.stderr}

        except subprocess.TimeoutExpired as e:
            logger.error(f"Git command timed out: {' '.join(command)}")
            raise GitTimeoutError(f"Command timed out after {timeout} seconds") from e

        except Exception as e:
            logger.error(f"Git command error: {str(e)}")
            raise GitCommandError(str(e)) from e


class RepositoryManager:
    """레포지토리 경로 관리를 담당하는 클래스"""

    def __init__(self, base_path: str = "repository") -> None:
        """
        RepositoryManager 초기화

        Args:
            base_path: 레포지토리를 저장할 기본 경로
        """
        # 현재 작업 디렉토리 기준으로 상대 경로 해석
        # Celery worker가 어디서 실행되든 프로젝트 루트의 repository 사용
        if Path(base_path).is_absolute():
            self.base_path: Path = Path(base_path)
        else:
            # 프로젝트 루트 찾기 (pyproject.toml 기준)
            current = Path.cwd()
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    self.base_path = current / base_path
                    break
                current = current.parent
            else:
                # pyproject.toml을 못 찾으면 현재 디렉토리 기준
                self.base_path = Path(base_path).resolve()

        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_repo_path(self, repo_name: str) -> Path:
        """
        레포지토리 경로 반환

        Args:
            repo_name: 레포지토리 이름

        Returns:
            레포지토리 절대 경로
        """
        return self.base_path / repo_name

    def exists(self, repo_name: str) -> bool:
        """
        레포지토리 존재 여부 확인

        Args:
            repo_name: 레포지토리 이름

        Returns:
            존재 여부
        """
        return self.get_repo_path(repo_name).exists()

    def validate_exists(self, repo_name: str) -> None:
        """
        레포지토리 존재 여부 검증

        Args:
            repo_name: 레포지토리 이름

        Raises:
            RepositoryNotFoundError: 레포지토리가 없을 때
        """
        if not self.exists(repo_name):
            raise RepositoryNotFoundError(f"Repository {repo_name} not found")

    def validate_not_exists(self, repo_name: str) -> None:
        """
        레포지토리 미존재 여부 검증

        Args:
            repo_name: 레포지토리 이름

        Raises:
            RepositoryAlreadyExistsError: 레포지토리가 이미 있을 때
        """
        if self.exists(repo_name):
            raise RepositoryAlreadyExistsError(f"Repository {repo_name} already exists")


class GitService:
    """Git 작업을 처리하는 서비스 클래스"""

    def __init__(self, base_repository_path: str = "repository") -> None:
        """
        GitService 초기화

        Args:
            base_repository_path: 레포지토리를 저장할 기본 경로
        """
        self.repo_manager: RepositoryManager = RepositoryManager(base_repository_path)
        self.command_runner: GitCommandRunner = GitCommandRunner()

    def clone_repository(self, git_url: str, repo_name: Optional[str] = None) -> CloneResult:
        """
        Git 레포지토리 클론

        Args:
            git_url: Git 레포지토리 URL
            repo_name: 저장할 레포지토리 이름 (없으면 URL에서 추출)

        Returns:
            클론 결과
        """
        try:
            # repo_name이 없으면 URL에서 추출
            if not repo_name:
                repo_name = git_url.split("/")[-1].replace(".git", "")

            # 이미 존재하는지 확인
            self.repo_manager.validate_not_exists(repo_name)

            repo_path = self.repo_manager.get_repo_path(repo_name)

            # Git clone 실행
            logger.info(f"Cloning repository: {git_url} -> {repo_name}")
            self.command_runner.run(["git", "clone", git_url, str(repo_path)])

            logger.info(f"Repository cloned successfully: {repo_name}")
            return CloneResult(
                success=True,
                repo_name=repo_name,
                repo_path=str(repo_path),
                message="Repository cloned successfully",
                error=None,
            )

        except (RepositoryAlreadyExistsError, GitCommandError, GitTimeoutError) as e:
            logger.error(f"Clone repository error: {str(e)}")
            return CloneResult(
                success=False,
                repo_name=repo_name or "",
                repo_path="",
                message=None,
                error=str(e),
            )

    def check_commit_status(self, repo_name: str) -> StatusResult:
        """
        레포지토리 커밋 상태 확인

        Args:
            repo_name: 레포지토리 이름

        Returns:
            커밋 상태 정보
        """
        try:
            # 레포지토리 존재 확인
            self.repo_manager.validate_exists(repo_name)
            repo_path = self.repo_manager.get_repo_path(repo_name)

            # git status 실행
            status_result = self.command_runner.run(["git", "status", "--porcelain"], cwd=repo_path)

            # 최신 커밋 정보 가져오기
            log_result = self.command_runner.run(
                ["git", "log", "-1", "--pretty=format:%H|%an|%ae|%s|%ci"],
                cwd=repo_path,
            )

            # 브랜치 정보 가져오기
            branch_result = self.command_runner.run(["git", "branch", "--show-current"], cwd=repo_path)

            # 최신 커밋 정보 파싱
            commit_info: Optional[CommitInfo] = None
            if log_result["stdout"].strip():
                parts = log_result["stdout"].strip().split("|")
                if len(parts) == 5:
                    commit_info = CommitInfo(
                        hash=parts[0],
                        author_name=parts[1],
                        author_email=parts[2],
                        message=parts[3],
                        date=parts[4],
                    )

            return StatusResult(
                success=True,
                repo_name=repo_name,
                repo_path=str(repo_path),
                branch=branch_result["stdout"].strip(),
                has_changes=bool(status_result["stdout"].strip()),
                status=status_result["stdout"],
                latest_commit=commit_info,
                error=None,
            )

        except (RepositoryNotFoundError, GitCommandError, GitTimeoutError) as e:
            logger.error(f"Check commit status error: {str(e)}")
            return StatusResult(
                success=False,
                repo_name=repo_name,
                repo_path="",
                branch="",
                has_changes=False,
                status="",
                latest_commit=None,
                error=str(e),
            )

    def pull_repository(self, repo_name: str) -> PullResult:
        """
        레포지토리 pull (업데이트)

        Args:
            repo_name: 레포지토리 이름

        Returns:
            Pull 결과
        """
        try:
            # 레포지토리 존재 확인
            self.repo_manager.validate_exists(repo_name)
            repo_path = self.repo_manager.get_repo_path(repo_name)

            # git pull 실행
            logger.info(f"Pulling repository: {repo_name}")
            result = self.command_runner.run(["git", "pull"], cwd=repo_path)

            logger.info(f"Repository pulled successfully: {repo_name}")
            return PullResult(
                success=True,
                repo_name=repo_name,
                repo_path=str(repo_path),
                message=result["stdout"],
                error=None,
            )

        except (RepositoryNotFoundError, GitCommandError, GitTimeoutError) as e:
            logger.error(f"Pull repository error: {str(e)}")
            return PullResult(
                success=False, repo_name=repo_name, repo_path="", message=None, error=str(e)
            )

    def delete_repository(self, repo_name: str) -> DeleteResult:
        """
        레포지토리 삭제

        Args:
            repo_name: 레포지토리 이름

        Returns:
            삭제 결과
        """
        try:
            # 레포지토리 존재 확인
            self.repo_manager.validate_exists(repo_name)
            repo_path = self.repo_manager.get_repo_path(repo_name)

            # 디렉토리 삭제 (Windows 읽기 전용 파일 처리)
            logger.info(f"Deleting repository: {repo_name}")

            def remove_readonly(func: Any, path: str, exc_info: Any) -> None:
                """읽기 전용 파일 삭제를 위한 에러 핸들러"""
                os.chmod(path, stat.S_IWRITE)
                func(path)

            shutil.rmtree(repo_path, onerror=remove_readonly)

            logger.info(f"Repository deleted successfully: {repo_name}")
            return DeleteResult(
                success=True,
                repo_name=repo_name,
                message=f"Repository {repo_name} deleted successfully",
                error=None,
            )

        except (RepositoryNotFoundError, Exception) as e:
            logger.error(f"Delete repository error: {str(e)}")
            return DeleteResult(success=False, repo_name=repo_name, message=None, error=str(e))
