# src/pages/repository_page/data_manager.py
import json
import os

def _get_json_path(repo_name: str) -> str:
    #TODO 리팩토링 필요
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))))
    return os.path.join(project_root, 'git-agent3', 'parsed_repository', repo_name, 'GitaiData.json')

def load_data_from_json(repo_name: str) -> dict:
    file_path = _get_json_path(repo_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_data_to_json(repo_name: str, data: dict):
    file_path = _get_json_path(repo_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"데이터 저장 오류: {e}")