# src/pages/repository_page/repository_page.py
from nicegui import ui
from datetime import datetime
from .data_manager import load_data_from_json, save_data_to_json
from .sidebar import sidebar
from .chat_area import chat_area
from src.apis.repository_page.api import request
import json

#TODO 전체적인 소스코드 리팩토링 필요
#TODO 전체적인 소스코드 리팩토링 필요
#TODO 전체적인 소스코드 리팩토링 필요

def render_repository_page(repo_name: str):
    data = load_data_from_json(repo_name)
    state = {
        'branch': next(iter(data), None),
        'room': None
    }


    def on_branch_change(branch: str):
        state['branch'] = branch
        state['room'] = None
        ui.navigate.to(f'/project/{repo_name}')

    def render_messages():
        message_area.clear()
        branch, room = state['branch'], state['room']
        if branch and room and room in data.get(branch, {}):
            with message_area:
                for msg in data[branch][room]:
                    content = msg.get('content', '')
                    msg_type = msg.get('type', '')

                    # Check if the content is a list (JSON response)
                    if isinstance(content, list):
                        output_text = "🔎 **검색 결과**\n"

                        # Process each item in the list
                        for item in content:
                            # Extract the 'text' field, which is a JSON string
                            text_str = item.get('text', '{}')
                            try:
                                # Parse the inner JSON string
                                inner_json = json.loads(text_str)

                                # Extract relevant fields
                                file_path = inner_json.get('file_path', 'N/A')
                                function_name = inner_json.get('name', 'N/A')
                                code = inner_json.get('code', 'N/A')

                                # Format the output for better readability
                                output_text += (
                                    f"---"
                                    f"📂 **파일**: {file_path}\n"
                                    f"📜 **함수**: `{function_name}`\n"
                                    f"```python\n{code}\n```\n"
                                )
                            except json.JSONDecodeError:
                                output_text += f"⚠️ 데이터 처리 오류: {text_str}\n"

                    # Check if the content is a string (simple message)
                    elif isinstance(content, str):
                        output_text = content

                    else:
                        output_text = "⚠️ 지원하지 않는 메시지 형식입니다."

                    ui.chat_message(
                        text=output_text,
                        name=msg_type,
                        stamp=msg.get('create_date', ''),
                        sent=msg_type == 'user'
                    ).classes('w-full')

    def on_room_open(room: str):
        state['room'] = room
        chat_title.set_text(f"[{state['branch']}] ▸ [{room}]")
        render_messages()
        chat_input.enable()
        send_button.enable()

    async def send_message():
        nonlocal data
        branch, room, text = state['branch'], state['room'], chat_input.value.strip()
        if not (branch and room and text): return
        id = len(data[branch][room]) + 1

        new_message = {"type": "user", "content": text, "create_date": datetime.now().strftime("%Y%m%d%H%M"),
                       "id": id}
        data[branch][room].append(new_message)
        save_data_to_json(repo_name, data)

        api_response = await request(user_message=text,branch=branch,room=room , id = id)
        data = load_data_from_json(repo_name)
        render_messages()
        chat_input.value = ''


    def create_new_room():
        new_room_name, branch = new_room_input.value.strip(), state['branch']
        if not new_room_name:
            return ui.notify('채팅방 이름을 입력해주세요.', color='negative')
        if new_room_name in data.get(branch, {}):
            return ui.notify('이미 존재하는 채팅방 이름입니다.', color='negative')

        initial_message = {"type": "GitAI", "content": "무엇이 궁금하신가요?",
                           "create_date": datetime.now().strftime("%Y%m%d%H%M"), "id": 1}
        data[branch][new_room_name] = [initial_message]
        save_data_to_json(repo_name, data)

        create_room_dialog.close()
        ui.navigate.to(f'/project/{repo_name}')
        ui.notify(f"'{new_room_name}' 채팅방이 생성되었습니다.", color='positive')

    with ui.dialog() as create_room_dialog, ui.card():
        ui.label('새 채팅방 생성').classes('text-xl font-bold')
        new_room_input = ui.input(label='채팅방 주제').props('autofocus').classes('w-full')
        with ui.row().classes('w-full justify-end'):
            ui.button('취소', on_click=create_room_dialog.close, color='grey')
            ui.button('생성', on_click=create_new_room)

    with ui.row().style('height:100vh; width:100vw;'):
        sidebar(
            repo_name=repo_name, data=data, current_branch=state['branch'],
            on_room_open=on_room_open, on_branch_change=on_branch_change,
            on_create_room_click=create_room_dialog.open
        )
        with ui.column().style('flex:1; padding:20px;'):
            chat_title, message_area, chat_input, send_button = chat_area()

            if not state['room']:
                chat_input.disable()
                send_button.disable()

            with ui.row().style('align-items: flex-start; width: 100%;'):
                chat_input.style('flex-grow: 1;')
                send_button.on('click', send_message)