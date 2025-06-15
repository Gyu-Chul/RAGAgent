import os
import json
import sys
import subprocess  # subprocess 모듈 추가


def parse_single_js_file(file_path: str) -> list:
    """
    Node.js 파서 스크립트를 호출하여 JavaScript 파일을 분석하고
    그 결과를 JSON(list of dicts)으로 반환합니다.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # parser.js 파일의 경로를 현재 스크립트 기준으로 설정
    parser_script_path = os.path.join(os.path.dirname(__file__), 'parser.js')

    if not os.path.isfile(parser_script_path):
        raise FileNotFoundError(f"Node.js parser script not found at: {parser_script_path}")

    # Node.js 스크립트를 subprocess로 실행
    command = ['node', parser_script_path, os.path.abspath(file_path)]

    try:
        # check=True: Node.js 스크립트에서 오류 발생 시 예외를 발생시킴
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        # Node.js 스크립트의 표준 출력을 JSON으로 파싱하여 반환
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("Node.js is not installed or not in the system's PATH.")
    except subprocess.CalledProcessError as e:
        # Node.js 스크립트 실행 중 발생한 오류를 출력
        raise RuntimeError(f"Error executing Node.js parser script for {file_path}:\n{e.stderr}")
    except json.JSONDecodeError:
        raise ValueError(f"Failed to decode JSON from Node.js parser output for {file_path}.")


def process_js_directory(input_dir: str, output_dir: str) -> None:
    """
    `input_dir`에 있는 모든 `.js` 파일을 재귀 탐색하여,
    결과를 `output_dir` 구조에 맞게 `.json`로 저장합니다.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"[ERROR] 입력 디렉토리가 아닙니다: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    for root, dirs, files in os.walk(input_dir):
        if '.git' in dirs:
            dirs.remove('.git')

        for f in files:
            if f.endswith('.js'):
                src_path = os.path.join(root, f)
                rel_path = os.path.relpath(src_path, input_dir)
                out_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + '.json')

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                try:
                    entries = parse_single_js_file(src_path)
                    if entries:
                        with open(out_path, 'w', encoding='utf-8') as of:
                            json.dump(entries, of, ensure_ascii=False, indent=2)
                        print(f"[OK] 생성됨: {out_path}")

                except Exception as e:
                    print(f"[ERROR] 처리 실패: {src_path} → {e}", file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("사용법: python js_parse1.py <input_directory> <output_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        process_js_directory(input_path, output_path)
        print("\nJavaScript 디렉토리 파싱 완료.")
    except Exception as e:
        print(f"[최종 에러] {e}", file=sys.stderr)
        sys.exit(1)