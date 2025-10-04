"""
Git Service 예외 클래스 정의
"""


class GitServiceError(Exception):
    """Git Service 기본 예외 클래스"""

    pass


class RepositoryNotFoundError(GitServiceError):
    """레포지토리를 찾을 수 없을 때 발생하는 예외"""

    pass


class RepositoryAlreadyExistsError(GitServiceError):
    """레포지토리가 이미 존재할 때 발생하는 예외"""

    pass


class GitCommandError(GitServiceError):
    """Git 명령어 실행 실패 시 발생하는 예외"""

    pass


class GitTimeoutError(GitServiceError):
    """Git 명령어 타임아웃 시 발생하는 예외"""

    pass
