from nicegui import ui
import httpx  # 비동기 HTTP 클라이언트

async def gitclone(inp):
    repo_url = inp.value
    if not repo_url:
        ui.notify("레포지토리 주소를 입력하세요", type='warning')
        return

    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')

    payload = {
        "type": "GITCLONE",
        "content": repo_url,
        "name": repo_name,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/api/file_flag/addTask",
                json=payload
            )
            result = response.json()
            print("API 응답:", result)
            ui.notify(f"로딩중...: {result}")

    except Exception as e:
        print("오류 발생:", e)
        ui.notify(f"요청 실패: {e}", type='negative')