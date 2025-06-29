from nicegui import ui
from src.components.sidebar import sidebar, state as sidebar_state
from src.components.chat_area import chat_area

# JSON 더미 데이터 로드
data = {"test":"Test"}

def render_project(repo_name: str):
    # 브랜치 변경 콜백
    def on_branch_change(branch: str):
        sidebar_state['branch'] = branch
        sidebar_state['room'] = None
        ui.navigate.to(f'/project/{repo_name}')

    # 채팅방 선택 콜백
    def on_room_open(room: str):
        sidebar_state['room'] = room
        chat_title.set_text(f'[{sidebar_state["branch"]}] ▸ [{room}]')
        message_area.clear()
        for msg in data[sidebar_state['branch']][room]:
            with message_area:
                ui.label(msg).style('margin-bottom:8px;')
        chat_input.enable()
        send_button.enable()

    # 메시지 전송 콜백
    def send_message():
        room = sidebar_state['room']
        text = chat_input.value.strip()
        if room and text:
            data[sidebar_state['branch']][room].append(text)
            with message_area:
                ui.label(text).style('margin-bottom:8px;')
            chat_input.value = ''

    # 페이지 레이아웃
    with ui.row().style('height:100vh; width:100vw;'):
        sidebar(repo_name, on_room_open=on_room_open, on_branch_change=on_branch_change)
        with ui.column().style('flex:1; padding:20px; justify-content:flex-start;'):
            # 채팅 영역 생성
            chat_title, message_area, chat_input, send_button = chat_area()
            chat_input.disable()
            send_button.disable()

            # 입력창과 전송 버튼을 같은 행에 배치
            with ui.row():
                chat_input
                send_button.on('click', lambda _: send_message())