import ast
import os
import sys
import json
from typing import List, Dict, Union

def parse_python_source_fully(
    file_path: str
) -> List[Dict[str, Union[str,int]]]:
    """
    주어진 Python 파일을 AST로 파싱하여,
    1) 최상단 연속된 import 블록 → type="module"
    2) 그 외 함수/클래스 바깥(top-level)에 위치한 연속된 실행문 → type="script"
    3) 동기 함수 정의(FunctionDef) → type="function"
    4) 비동기 함수 정의(AsyncFunctionDef) → type="async_function"
    5) 클래스 정의(ClassDef) → type="class"

    를 모두 추출하여, 각 블록을 다음과 같은 딕셔너리로 반환합니다:
      {
        "type": "<module|script|function|async_function|class>",
        "name": "<함수명/클래스명>" 또는 "" (module/script인 경우),
        "start_line": <시작 라인>,
        "end_line": <종료 라인>,
        "code": "<해당 블록 전체 소스>",
        "file_path": "<원본 파일 경로>"
      }
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


def process_directory(input_dir: str, output_dir: str) -> None:
    """
    `input_dir`에 있는 모든 `.py` 파일을 재귀 탐색하여,
    `parse_python_source_fully` 결과를 `output_dir` 구조에 맞게 `.json`로 저장합니다.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"[ERROR] 입력 디렉토리가 아닙니다: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)
    for root, dirs, files in os.walk(input_dir):
        rel = os.path.relpath(root, input_dir)
        tgt = output_dir if rel == '.' else os.path.join(output_dir, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            if not f.endswith('.py'):
                continue
            src_path = os.path.join(root, f)
            try:
                entries = parse_python_source_fully(src_path)
            except Exception as e:
                print(f"[WARN] 파싱 실패: {src_path} → {e}", file=sys.stderr)
                continue
            out_file = os.path.splitext(f)[0] + '.json'
            out_path = os.path.join(tgt, out_file)
            try:
                with open(out_path, 'w', encoding='utf-8') as of:
                    json.dump(entries, of, ensure_ascii=False, indent=2)
                print(f"[OK] 생성됨: {out_path}")
            except Exception as e:
                print(f"[ERROR] 저장 실패: {out_path} → {e}", file=sys.stderr)


def parse_json(name: str) -> str:
    """
    주어진 `input_dir` 이름을 기반으로, `repository/<input_dir>` 경로에서 파이썬 파일을 탐색하고,
    `parsed_repository/<output_dir>` 경로에 JSON 결과물을 생성합니다.

    Args:
        name (str): json 으로 변환할 레포지토리 이름

    Returns:
        str: 성공 시 "SUCCESS", 실패 시 "FAILURE"
    """
    base_in = os.path.join('repository', name)
    base_out = os.path.join('parsed_repository', name)
    try:
        print(f"Parsing from {base_in} to {base_out}")
        process_directory(base_in, base_out)
        print(f"[SUCCESS] {name} --> json 변환 완료됨")
        return "SUCCESS"
    except Exception as e:
        print(f"[ERROR] 처리 실패: {e}", file=sys.stderr)
        return "FAILURE"
