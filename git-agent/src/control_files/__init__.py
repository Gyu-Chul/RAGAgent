import os
import json
from src.parse_json.parse_json import parse_json
from src.parse_json2.parse_json2 import parse_json2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPO_BASE_DIR = os.path.join(PROJECT_ROOT, 'repository')
PARSED_BASE_DIR = os.path.join(PROJECT_ROOT, 'parsed_repository')


def process_repository_files(repo_name: str):
    print(f"'{repo_name}' 경로에서 소스 코드 파일 탐색을 시작합니다.")
    repo_path = os.path.join(REPO_BASE_DIR, repo_name)
    if not os.path.isdir(repo_path):
        print(f"[오류] 경로를 찾을 수 없습니다: '{repo_path}'")
        return "FAILURE: Invalid path"

    js_directories_to_parse = set()

    for root, dirs, files in os.walk(repo_path):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')

        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                try:
                    print(f"파이썬 파일 발견: {file_path}")
                    parse_json(file_path)
                except Exception as e:
                    print(f"[오류] '{file_path}' 파이썬 파일 처리 중 오류: {e}")

        if any(f.endswith('.js') for f in files):
            js_directories_to_parse.add(root)

    if js_directories_to_parse:
        print(f"\n총 {len(js_directories_to_parse)}개의 자바스크립트 디렉토리를 파싱합니다.")
        for js_dir in sorted(list(js_directories_to_parse)):
            try:
                parse_json2(js_dir)
            except Exception as e:
                print(f"[오류] '{js_dir}' 자바스크립트 디렉토리 처리 중 오류: {e}")

    parsed_repo_path = os.path.join(PARSED_BASE_DIR, repo_name)
    os.makedirs(parsed_repo_path, exist_ok=True)
    git_ai_data_path = os.path.join(parsed_repo_path, 'GitAiData.json')
    data = {"main": {}}
    try:
        with open(git_ai_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nGitAiData.json 파일 생성 완료: {git_ai_data_path}")
    except Exception as e:
        print(f"[오류] GitAiData.json 생성 중 오류: {e}")

    print("\n모든 소스 코드 파일 처리가 완료되었습니다.")
    return "SUCCESS"