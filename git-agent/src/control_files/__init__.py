# git-agent/src/control_files/__init__.py

import os
# parse_json 함수가 위치한 경로를 정확하게 지정해야 합니다.
from src.parse_json.parse_json import parse_json


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPO_BASE_DIR = os.path.join(PROJECT_ROOT, 'repository')

def process_python_files_in_repo(repo_name: str):
    """
    주어진 레포지토리 경로를 탐색하여 모든 파이썬(.py) 파일을 찾아
    parse_json 함수로 파싱을 요청합니다.

    Args:
        repo_name (str): 로컬에 클론된 레포지토리의 전체 경로입니다.
    """
    print(f"'{repo_name}' 경로에서 파이썬 파일 탐색을 시작합니다.")
    repo_path = os.path.join(REPO_BASE_DIR, repo_name)
    print(f"자동으로 완성된 전체 경로: '{repo_path}'")
    if not os.path.isdir(repo_path):
        print(f"[오류] 제공된 경로 '{repo_path}'를 찾을 수 없거나 디렉터리가 아닙니다.")
        print("핸들러에서 전달하는 경로가 올바른지 확인해주세요.")
        return "FAILURE: Invalid path"

    # os.walk를 사용하여 디렉토리 하위의 모든 파일을 순회합니다.
    for root, _, files in os.walk(repo_path):
        print("작동")
        for filename in files:
            # 파일의 확장자가 .py 인지 확인합니다.
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                try:
                    print(f"파이썬 파일 발견: {file_path}")
                    # parse_json 함수를 파일 경로와 함께 호출합니다.
                    parse_json(file_path)
                except Exception as e:
                    print(f"'{file_path}' 파일 파싱 중 오류 발생: {e}")

    print("모든 파이썬 파일 처리가 완료되었습니다.")
    return "SUCCESS"