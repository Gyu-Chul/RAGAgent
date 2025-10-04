"""
Python Parser 관련 타입 정의
"""

from typing import TypedDict, List, Dict, Any, Union, Optional


class ChunkEntry(TypedDict):
    """청킹된 코드 블록 정보"""

    type: str  # "module", "script", "function", "async_function", "class"
    name: str
    start_line: int
    end_line: int
    code: str
    file_path: str


class ParseResult(TypedDict):
    """파일 파싱 결과 타입"""

    success: bool
    file_path: str
    chunks: List[ChunkEntry]
    error: Optional[str]


class RepositoryParseResult(TypedDict):
    """레포지토리 전체 파싱 결과 타입"""

    success: bool
    repo_name: str
    repo_path: str
    total_files: int
    parsed_files: int
    failed_files: int
    total_chunks: int
    output_path: str
    files: List[ParseResult]
    error: Optional[str]
