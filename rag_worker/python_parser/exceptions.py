"""
Python Parser 예외 클래스 정의
"""


class PythonParserError(Exception):
    """Python Parser 기본 예외 클래스"""

    pass


class FileNotFoundError(PythonParserError):
    """파일을 찾을 수 없을 때 발생하는 예외"""

    pass


class ParseError(PythonParserError):
    """파싱 실패 시 발생하는 예외"""

    pass


class InvalidRepositoryError(PythonParserError):
    """유효하지 않은 레포지토리일 때 발생하는 예외"""

    pass
