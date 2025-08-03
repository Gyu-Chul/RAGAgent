# src/components/repository_page/api_call.py
import httpx
from nicegui import ui

#TODO 전체적인 소스코드 리팩토링 필요

async def request(user_message: str,branch , room, id ):
    api_url = "http://127.0.0.1:8000/api/chat/request"
    print(user_message,branch,room,id)
    # payload = {
    #     "message": user_message
    # }

    try:
        async with httpx.AsyncClient() as client:

            # response = await client.post(api_url, json=payload, timeout=10.0)


            params = {"message": user_message , "branch" : branch , "room" : room , "id" : id}
            response = await client.get(api_url, params=params, timeout=10.0)


            response.raise_for_status()

            ui.notify(f"API 호출 성공: {response.status_code}", color='positive')
            return response.json()

    except httpx.HTTPStatusError as e:
        ui.notify(f"API 오류 발생: {e.response.status_code}", color='negative')
        print(f"HTTP Error: {e}")
        return None
    except httpx.RequestError as e:
        ui.notify("API 서버에 연결할 수 없습니다.", color='negative')
        print(f"Request Error: {e}")
        return None
    except Exception as e:
        ui.notify("알 수 없는 오류가 발생했습니다.", color='negative')
        print(f"An unexpected error occurred: {e}")
        return None