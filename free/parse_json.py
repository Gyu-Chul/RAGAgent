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

    # 1) 원본 파일을 읽어서 한 줄씩 리스트에 보관
    with open(file_path, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()
    source_code = ''.join(source_lines)

    # 2) AST 파싱
    try:
        tree = ast.parse(source_code)
    except Exception as e:
        raise SyntaxError(f"[ERROR] AST 파싱 실패: {e}")

    entries: List[Dict[str, Union[str,int]]] = []

    # 3) 최상단 연속된 import 블록 추출
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

    # 4) 최상위바디(tree.body)에서 "함수/클래스 외(top-level) 노드"를 모아서 스크립트 블록으로 묶기
    top_level_segments = []
    segment_start = None
    segment_end   = None

    for node in tree.body:
        # import, function, async function, class 정의는 script 블록이 아님
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if segment_start is not None:
                top_level_segments.append((segment_start, segment_end))
                segment_start = None
                segment_end   = None
            continue

        # 그 외 노드는 top-level 실행문
        if segment_start is None:
            segment_start = node.lineno
            segment_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        else:
            new_start = node.lineno
            new_end   = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            if new_start <= segment_end + 1:
                segment_end = max(segment_end, new_end)
            else:
                top_level_segments.append((segment_start, segment_end))
                segment_start = new_start
                segment_end   = new_end

    if segment_start is not None:
        top_level_segments.append((segment_start, segment_end))

    for start_line, end_line in top_level_segments:
        # import 블록과 겹치는 부분은 건너뛰기
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

    # 5) 동기 함수 정의 탐색
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line   = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            code_snip  = ''.join(source_lines[start_line-1 : end_line])
            entries.append({
                "type": "function",
                "name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "code": code_snip.rstrip('\n'),
                "file_path": file_path
            })

    # 6) 비동기 함수 정의 탐색
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            start_line = node.lineno
            end_line   = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            code_snip  = ''.join(source_lines[start_line-1 : end_line])
            entries.append({
                "type": "async_function",
                "name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "code": code_snip.rstrip('\n'),
                "file_path": file_path
            })

    # 7) 클래스 정의 탐색
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start_line = node.lineno
            end_line   = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            code_snip  = ''.join(source_lines[start_line-1 : end_line])
            entries.append({
                "type": "class",
                "name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "code": code_snip.rstrip('\n'),
                "file_path": file_path
            })

    return entries


def process_directory(input_dir: str, output_dir: str) -> None:
    """
    input_dir 내의 모든 .py 파일을 재귀적으로 탐색하여,
    parse_python_source_fully() 결과를 output_dir에 동일한 구조로 .json 파일로 저장한다.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"[ERROR] 입력 디렉토리가 아닙니다: {input_dir}")

    # output_dir이 존재하지 않으면 생성
    os.makedirs(output_dir, exist_ok=True)

    # os.walk로 input_dir 내 모든 서브 디렉토리와 파일 탐색
    for root, dirs, files in os.walk(input_dir):
        # 현재 root에 대응되는 output 디렉토리 경로
        rel_root = os.path.relpath(root, input_dir)
        if rel_root == '.':
            target_root = output_dir
        else:
            target_root = os.path.join(output_dir, rel_root)

        # output 하위에 동일한 서브디렉토리 구조가 없으면 생성
        os.makedirs(target_root, exist_ok=True)

        for fname in files:
            if not fname.endswith('.py'):
                continue

            # 처리할 .py 파일의 전체 경로
            py_path = os.path.join(root, fname)

            try:
                parsed_entries = parse_python_source_fully(py_path)
            except Exception as e:
                print(f"[WARN] 파싱 실패: {py_path} → {e}", file=sys.stderr)
                continue

            # 상대경로 + 확장자를 .json 으로 바꿔서 output 경로 생성
            base_name = os.path.splitext(fname)[0]  # 예: "module.py" → "module"
            json_fname = base_name + ".json"
            json_path = os.path.join(target_root, json_fname)

            # JSON으로 저장
            try:
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(parsed_entries, jf, ensure_ascii=False, indent=2)
                print(f"[OK] 생성됨: {json_path}")
            except Exception as e:
                print(f"[ERROR] JSON 저장 실패: {json_path} → {e}", file=sys.stderr)


if __name__ == "__main__":
    # 사용 예시: python parse_json.py <input_dir> <output_dir>
    if len(sys.argv) != 3:
        print("사용법: python parse_json.py  <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    process_directory(input_dir, output_dir)
