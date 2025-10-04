"""
Python AST 파서 - AST를 이용한 Python 파일 분석
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Union

from .types import ChunkEntry

logger = logging.getLogger(__name__)


class PythonASTParser:
    """Python 파일을 AST로 파싱하여 청킹하는 클래스"""

    @staticmethod
    def parse_file(file_path: Path) -> List[ChunkEntry]:
        """
        주어진 Python 파일을 AST로 파싱하여 청킹

        Args:
            file_path: 파싱할 Python 파일 경로

        Returns:
            청킹된 코드 블록 리스트

        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때
            SyntaxError: AST 파싱 실패 시
        """
        if not file_path.is_file():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            source_lines = f.readlines()
        source_code = "".join(source_lines)

        try:
            tree = ast.parse(source_code)
        except Exception as e:
            raise SyntaxError(f"AST 파싱 실패: {e}") from e

        entries: List[ChunkEntry] = []
        file_path_str = str(file_path)

        # 1. Import 블록 추출 (type="module")
        import_nodes = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_nodes.append(node)
            else:
                break

        last_import_end = 0
        if import_nodes:
            start_line = import_nodes[0].lineno
            end_line = (
                import_nodes[-1].end_lineno
                if hasattr(import_nodes[-1], "end_lineno")
                else import_nodes[-1].lineno
            )
            code_snip = "".join(source_lines[start_line - 1 : end_line])
            entries.append(
                ChunkEntry(
                    type="module",
                    name="",
                    start_line=start_line,
                    end_line=end_line,
                    code=code_snip.rstrip("\n"),
                    file_path=file_path_str,
                )
            )
            last_import_end = end_line

        # 2. Top-level 스크립트 블록 추출 (type="script")
        top_segments = PythonASTParser._extract_top_level_segments(tree)

        for start_line, end_line in top_segments:
            if end_line <= last_import_end:
                continue
            code_snip = "".join(source_lines[start_line - 1 : end_line])
            entries.append(
                ChunkEntry(
                    type="script",
                    name="",
                    start_line=start_line,
                    end_line=end_line,
                    code=code_snip.rstrip("\n"),
                    file_path=file_path_str,
                )
            )

        # 3. 함수 정의 추출 (type="function")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                sl = node.lineno
                el = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                snippet = "".join(source_lines[sl - 1 : el])
                entries.append(
                    ChunkEntry(
                        type="function",
                        name=node.name,
                        start_line=sl,
                        end_line=el,
                        code=snippet.rstrip("\n"),
                        file_path=file_path_str,
                    )
                )

        # 4. 비동기 함수 정의 추출 (type="async_function")
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                sl = node.lineno
                el = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                snippet = "".join(source_lines[sl - 1 : el])
                entries.append(
                    ChunkEntry(
                        type="async_function",
                        name=node.name,
                        start_line=sl,
                        end_line=el,
                        code=snippet.rstrip("\n"),
                        file_path=file_path_str,
                    )
                )

        # 5. 클래스 정의 추출 (type="class")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                sl = node.lineno
                el = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                snippet = "".join(source_lines[sl - 1 : el])
                entries.append(
                    ChunkEntry(
                        type="class",
                        name=node.name,
                        start_line=sl,
                        end_line=el,
                        code=snippet.rstrip("\n"),
                        file_path=file_path_str,
                    )
                )

        return entries

    @staticmethod
    def _extract_top_level_segments(tree: ast.AST) -> List[tuple[int, int]]:
        """
        Top-level 스크립트 블록 추출

        Args:
            tree: AST 트리

        Returns:
            (start_line, end_line) 튜플 리스트
        """
        top_segments: List[tuple[int, int]] = []
        seg_start = None
        seg_end = None

        for node in tree.body:
            # Import, 함수, 클래스는 건너뛰기
            if isinstance(
                node,
                (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                if seg_start is not None:
                    top_segments.append((seg_start, seg_end))
                    seg_start = None
                    seg_end = None
                continue

            # 스크립트 블록 시작 또는 확장
            if seg_start is None:
                seg_start = node.lineno
                seg_end = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
            else:
                ns = node.lineno
                ne = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
                if ns <= seg_end + 1:
                    seg_end = max(seg_end, ne)
                else:
                    top_segments.append((seg_start, seg_end))
                    seg_start, seg_end = ns, ne

        if seg_start is not None:
            top_segments.append((seg_start, seg_end))

        return top_segments


# 하위 호환성을 위한 함수 (기존 parse_json.py와 동일한 인터페이스)
def parse_python_source_fully(file_path: str) -> List[Dict[str, Union[str, int]]]:
    """
    주어진 Python 파일을 AST로 파싱하여 청킹 (레거시 호환 함수)

    Args:
        file_path: 파싱할 Python 파일 경로

    Returns:
        청킹된 코드 블록 리스트
    """
    parser = PythonASTParser()
    return parser.parse_file(Path(file_path))
