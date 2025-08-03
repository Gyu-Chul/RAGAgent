from fastapi import APIRouter, HTTPException
import os
import json
from datetime import datetime
from typing import Dict, List, Any

router = APIRouter()


def _get_json_path(repo_name: str) -> str:
    # TODO 리팩토링 필요
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))
    return os.path.join(project_root, 'git-agent', 'parsed_repository', repo_name, 'GitaiData.json')


def save_data_to_json(repo_name: str, data: Dict):
    file_path = _get_json_path(repo_name)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 폴더가 없을 경우 생성
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"데이터 저장 오류: {e}")


def load_data_from_json(repo_name: str) -> Dict:
    file_path = _get_json_path(repo_name)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/request", status_code=200)
async def request(message,branch: str, room: str,id):


    #일단 하드코딩이라, 이거 변수처리 필요함.
    repo_name = "git-ai-sample"

    # 1. JSON 데이터 로드
    data = load_data_from_json(repo_name)
    print(data)

    # 2. 데이터 검색 및 수정
    try:
        chat_list: List[Dict[str, Any]] = data.setdefault(branch, {}).setdefault(room, [])

        # 1. 새로운 ID 계산 (가장 마지막 ID를 찾아 + 1)
        if not chat_list:
            new_id = 1
        else:
            last_id = max(item.get('id', 0) for item in chat_list)
            new_id = last_id + 1

        # 2. 새로운 메시지 객체 생성
        new_message = {
            "type": "GitAI",  # 추가되는 메시지는 'user' 타입으로 가정
            "content": "메세지 수신 성공",
            "create_date": datetime.now().strftime("%Y%m%d%H%M%S"),  # YYYYMMDDHHMMSS 형식
            "id": new_id
        }

        # 3. 채팅 목록에 새로운 메시지 추가
        chat_list.append(new_message)
        print(f"Message Added: id={new_id}, content='{message}'")

    except KeyError:
        # branch나 room이 존재하지 않을 경우 404 에러 반환
        raise HTTPException(status_code=404, detail=f"Branch '{branch}' or Room '{room}' not found.")

    # 3. 변경된 데이터 저장
    save_data_to_json(repo_name, data)

    # 4. 성공 응답 반환
    return {"status": "success", "message": "GitAI content has been updated."}