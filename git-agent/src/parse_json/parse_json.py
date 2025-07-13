

import ast
import os
import sys
import json
from typing import List, Dict, Union


def parse_json(file_path: str) -> None:
    """
    파이썬 파일 경로(`file_path`) 하나를 받아 AST로 분석한 후,
    'parsed_repository' 폴더에 동일한 구조를 유지하며 .json 파일로 저장합니다.

    Args:
        file_path (str): 'repository' 폴더 내에 있는 파싱할 .py 파일의 전체 경로.
    """
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    REPO_BASE_DIR = os.path.join(PROJECT_ROOT, 'repository')
    PARSED_BASE_DIR = os.path.join(PROJECT_ROOT, 'parsed_repository')

    try:
        parsed_entries = parse_python_source_fully(file_path)
    except Exception as e:
        print(f"[WARN] 파일 파싱 실패: {file_path} → {e}", file=sys.stderr)
        return

    #    (예: .../repository/repo1/main.py  ->  .../parsed_repository/repo1/main.json)
    try:
        relative_path = os.path.relpath(file_path, REPO_BASE_DIR)
        json_output_path_py = os.path.join(PARSED_BASE_DIR, relative_path)
        json_output_path = os.path.splitext(json_output_path_py)[0] + '.json'
    except ValueError:
        print(f"[ERROR] 출력 경로 계산 실패: {file_path}", file=sys.stderr)
        return


    output_dir = os.path.dirname(json_output_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_entries, f, ensure_ascii=False, indent=2)
        print(f"[OK] 생성됨: {json_output_path}")
    except Exception as e:
        print(f"[ERROR] JSON 저장 실패: {json_output_path} → {e}", file=sys.stderr)


---------

def parse_python_source_fully(
    file_path: str
) -> List[Dict[str, Union[str, int]]]:
    """
    주어진 Python 파일을 AST로 파싱하여,
    1) 최상단 연속된 import 블록 → type="module"
    2) 그 외 함수/클래스 바깥(top-level)에 위치한 연속된 실행문 → type="script"
    3) 동기 함수 정의(FunctionDef) → type="function"
    4) 비동기 함수 정의(AsyncFunctionDef) → type="async_function"
    5) 클래스 정의(ClassDef) → type="class"

    를 모두 추출하여, 각 블록을 딕셔너리로 반환합니다.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()
    source_code = ''.join(source_lines)

    try:
        tree = ast.parse(source_code)
    except Exception as e:
        raise SyntaxError(f"[ERROR] AST 파싱 실패: {e}")

    entries: List[Dict[str, Union[str,int]]] = []
    import_nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
        else:
            break

    last_import_end = 0
    if import_nodes:
        start_line = import_nodes[0].lineno
        end_line = import_nodes[-1].end_lineno if hasattr(import_nodes[-1], 'end_lineno') else import_nodes[-1].lineno
        code_snip = ''.join(source_lines[start_line-1 : end_line])
        entries.append({
            "type": "module",
            "name": "",
            "start_line": start_line,
            "end_line": end_line,
            "code": code_snip.rstrip('\n'),
            "file_path": file_path
        })
        last_import_end = end_line

    top_segments = []
    seg_start = None
    seg_end = None
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if seg_start is not None:
                top_segments.append((seg_start, seg_end))
                seg_start = None
                seg_end = None
            continue
        if seg_start is None:
            seg_start = node.lineno
            seg_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        else:
            ns, ne = node.lineno, node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            if ns <= seg_end + 1:
                seg_end = max(seg_end, ne)
            else:
                top_segments.append((seg_start, seg_end))
                seg_start, seg_end = ns, ne
    if seg_start is not None:
        top_segments.append((seg_start, seg_end))

    for start_line, end_line in top_segments:
        if end_line <= last_import_end:
            continue
        code_snip = ''.join(source_lines[start_line-1 : end_line])
        entries.append({
            "type": "script",
            "name": "",
            "start_line": start_line,
            "end_line": end_line,
            "code": code_snip.rstrip('\n'),
            "file_path": file_path
        })

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            sl, el = node.lineno, node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            snippet = ''.join(source_lines[sl-1:el])
            entries.append({"type": "function", "name": node.name, "start_line": sl,
                            "end_line": el, "code": snippet.rstrip('\n'), "file_path": file_path})
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            sl, el = node.lineno, node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            snippet = ''.join(source_lines[sl-1:el])
            entries.append({"type": "async_function", "name": node.name, "start_line": sl,
                            "end_line": el, "code": snippet.rstrip('\n'), "file_path": file_path})
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            sl, el = node.lineno, node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            snippet = ''.join(source_lines[sl-1:el])
            entries.append({"type": "class", "name": node.name, "start_line": sl,
                            "end_line": el, "code": snippet.rstrip('\n'), "file_path": file_path})

    return entries