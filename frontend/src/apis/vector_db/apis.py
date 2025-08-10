# src/apis/vector_db/apis.py

import httpx
import json

# 백엔드 API 서버 주소 (필요시 수정)
BASE_URL = "http://127.0.0.1:8000/api/vectorDB"


async def _handle_response(response: httpx.Response):
    response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
    return response.json().get("message", "작업에 성공했으나 메시지가 없습니다.")


async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f'{BASE_URL}/connection_test')
            res.raise_for_status()
            return f"🧪 연결 테스트 결과: {res.json()['message']}"
    except Exception as e:
        return f'❌ 오류: {e}'


async def list_collections():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f'{BASE_URL}/list_collections')
            return await _handle_response(res)
    except Exception as e:
        return f'❌ 오류: {e}'


async def create_collection(collection_name: str, description: str, version: int):
    try:
        payload = {
            "collection_name": collection_name,
            "description": description,
            "version": version
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(f'{BASE_URL}/create_collection', json=payload)
            return await _handle_response(res)
    except Exception as e:
        return f'❌ 오류: {e}'
    

async def count_entities(collection_name: str):
    try:
        params = {"collection_name": collection_name}  # ✅ GET 요청은 params 사용
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/count_entities", params=params)
            return await _handle_response(res)
    except Exception as e:
        return f"❌ 오류: {e}"



async def delete_collection(collection_name: str):
    try:
        payload = {"collection_name": collection_name}
        async with httpx.AsyncClient() as client:
            res = await client.request("DELETE", f"{BASE_URL}/delete_collection", json=payload)
            return await _handle_response(res)
    except Exception as e:
        return f"❌ 오류: {e}"



async def delete_entity(collection_name: str, entity_id: str):
    try:
        payload = {
            "collection_name": collection_name,
            "entity_id": entity_id
        }
        async with httpx.AsyncClient() as client:
            res = await client.request("DELETE", f"{BASE_URL}/delete_entity", json=payload)
            return await _handle_response(res)
    except Exception as e:
        return f"❌ 오류: {e}"



async def view_entities(collection_name: str):
    try:
        params = {"collection_name": collection_name}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/view_entities", params=params)
            data = res.json()

        output_logs = []
        for idx, entity in enumerate(data.get("entities", []), 1):
            # ✅ 안전하게 필드 가져오기
            text_preview = entity.get("text") or entity.get("code") or "[NO TEXT]"
            text_preview = str(text_preview)[:100]

            log_entry = (
                f"[{idx}] ID: {entity.get('id')}\n"
                f"  Text: {text_preview}...\n"
                f"  Embedding dim: {entity.get('embedding_dim')}, "
                f"Preview: {entity.get('embedding_preview')}"
            )
            output_logs.append(log_entry)

        return "\n".join(output_logs) if output_logs else "조회된 엔티티가 없습니다."

    except Exception as e:
        return f"❌ 오류: {e}"



async def embed_json_file(collection_name: str, file_name: str, file_content):
    try:
        files = {'file': (file_name, file_content, 'application/json')}
        data = {'collection_name': collection_name}

        async with httpx.AsyncClient(timeout=3600.0) as client:
            res = await client.post(f'{BASE_URL}/embed_json_file', files=files, data=data)

        return res.json().get('message', '✅ 처리 완료')
    except Exception as e:
        return f'❌ 오류 발생: {e}'



async def search_basic(collection_name: str, query_text: str):
    try:
        params = {
            "collection_name": collection_name,
            "query_text": query_text
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/search_basic", params=params)
            return res.json().get("message", ""), res.json().get("results", [])
    except Exception as e:
        return f"❌ 오류: {e}", []


async def search_with_metadata(collection_name: str, query_text: str, metadata_filter: str):
    try:
        params = {
            "collection_name": collection_name,
            "query_text": query_text,
            "metadata_filter": metadata_filter
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/search_with_metadata", params=params)
            return res.json().get("message", ""), res.json().get("results", [])
    except Exception as e:
        return f"❌ 오류: {e}", []
