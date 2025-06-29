from nicegui import ui
import httpx

def http_call_button():
    # 결과를 표시할 라벨
    result_label = ui.label()

    async def get_api_data():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('http://127.0.0.1:8000/api/sample/test1')
                response.raise_for_status()
                result_label.set_text(f"API 응답: {response.text}")
        except httpx.RequestError as e:
            result_label.set_text(f"API 호출 오류: {e}")

    ui.button('API 호출', on_click=get_api_data)