from nicegui import ui
import json
from pathlib import Path

# JSON 더미 데이터 로드
DATA_FILE = Path(__file__).parent / 'chat_sample.json'
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    dummy_chat_data = json.load(f)

# 상태 저장
state = {
    'branch': 'Main1',
    'room': None
}

def render(repo_name: str):
    # 페이지 전체 레이아웃
    with ui.row().style('height:100vh; width:100vw;'):

        # ── 사이드바 ──
        with ui.column().style('width:260px; padding:20px; border-right:1px solid #ccc;'):

            # 홈으로 버튼
            ui.button('🏠 홈으로', on_click=lambda: ui.navigate.to('/'))\
              .style('margin-bottom:20px; width:100%;')

            # 레포 이름
            ui.label(repo_name)\
              .style('font-size:22px; font-weight:bold; margin-bottom:10px;')

            # 브랜치 선택
            def set_branch(b: str):
                state['branch'] = b
                state['room'] = None
                ui.navigate.to(f'/project/{repo_name}')

            for br in dummy_chat_data:
                color = 'red' if state['branch']==br else 'grey'
                ui.button(br.upper(), on_click=lambda b=br: set_branch(b))\
                  .props(f'flat color={color}')\
                  .style('width:100%; font-weight:bold; margin-bottom:10px;')

            ui.separator()
            ui.label('채팅방 목록')\
              .style('font-weight:bold; margin-top:10px;')

            # 채팅방 버튼
            for room in dummy_chat_data[state['branch']]:
                ui.button(room, on_click=lambda r=room: open_room(r))\
                  .style('width:100%; margin:5px 0;')

            # 새 채팅방 생성
            def create_room():
                with ui.dialog() as dlg, ui.card():
                    ui.label('새 채팅방 생성')
                    new_room = ui.input('채팅방 제목')
                    def add_room():
                        dummy_chat_data[state['branch']][new_room.value] = []
                        ui.notify(f'{new_room.value} 생성됨')
                        dlg.close()
                        ui.navigate.to(f'/project/{repo_name}')
                    ui.button('생성', on_click=add_room)
                    ui.button('닫기', on_click=dlg.close)
                dlg.open()

            ui.button('채팅방 생성', on_click=create_room)\
              .style('margin-top:20px;')

        # ── 메인 영역: 채팅 영역 ──
        with ui.column().style('flex:1; padding:20px; justify-content:flex-start;'):

            # **이제 이 안에서** chat_title, message_area, chat_input, send_button을 생성합니다.
            chat_title = ui.label('채팅방을 생성하거나 클릭하세요!')\
                          .style('color:#888; font-size:18px; margin-bottom:10px;')

            message_area = ui.column().style(
                'border:1px solid #ddd; border-radius:8px; '
                'padding:20px; height:400px; overflow-y:auto; margin-bottom:10px;'
            )

            chat_input = ui.input('채팅 입력란')\
                           .style('width:80%;')\
                           .props('outlined')
            chat_input.disable()

            send_button = ui.button('전송', on_click=None)\
                             .style('margin-left:10px;')
            send_button.disable()

            # 메시지 전송 로직
            def send_message():
                room = state['room']
                text = chat_input.value.strip()
                if room and text:
                    dummy_chat_data[state['branch']][room].append(text)
                    with message_area:
                        ui.label(text).style('margin-bottom:8px;')
                    chat_input.value = ""

            send_button.on('click', lambda _: send_message())

            # 채팅방 선택 시
            def open_room(room_name: str):
                state['room'] = room_name
                chat_title.set_text(f'[{state["branch"]}] ▸ [{room_name}]')
                message_area.clear()
                for msg in dummy_chat_data[state['branch']][room_name]:
                    with message_area:
                        ui.label(msg).style('margin-bottom:8px;')
                chat_input.enable()
                send_button.enable()

            # 전송 버튼과 입력창을 같은 행에
            with ui.row():
                chat_input
                send_button
