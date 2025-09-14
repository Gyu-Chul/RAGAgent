# src/pages/repository_page/chat_area.py
from nicegui import ui


def chat_area():
    with ui.column().style('width: 100%; height: calc(100vh - 150px);'):
        chat_title = ui.label("채팅방을 선택해주세요").style('font-size: 20px; font-weight: bold; margin-bottom: 10px;')
        message_area = ui.scroll_area().classes('w-full flex-grow border rounded-md p-4 bg-slate-100')

    chat_input = ui.textarea(placeholder="메시지를 입력하세요...").style('width: 100%;')
    send_button = ui.button('전송', icon='send')

    return chat_title, message_area, chat_input, send_button