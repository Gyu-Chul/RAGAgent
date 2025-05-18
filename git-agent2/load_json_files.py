from nicegui import ui
import json
from pathlib import Path

# JSON 데이터 불러오기
DATA_FILE = Path(__file__).parent / "chat_sample.json"
with open(DATA_FILE, "r", encoding="utf-8") as f:
    dummy_chat_data = json.load(f)

# 상태 저장
state = {
    'selected_branch': 'Main1',
    'selected_room': None
}


def render(repo_name: str):
    # 1) 채팅 입력창, 전송 버튼, 제목, 메시지 영역을 먼저 생성
    chat_title = ui.label("채팅방을 생성하거나 클릭하세요!") \
        .style("color: #888; font-size: 18px; margin-bottom: 10px;")

    message_area = ui.column().style(
        "border: 1px solid #ddd; border-radius: 8px; "
        "padding: 20px; height: 400px; overflow-y: auto; margin-bottom: 10px;"
    )

    chat_input = ui.input("채팅 입력란") \
        .style("width: 80%;") \
        .props("outlined") \
        .disable()

    send_button = ui.button("전송", on_click=None) \
        .style("margin-left: 10px;") \
        .disable()

    # 전송 로직 정의
    def send_message():
        room = state['selected_room']
        text = chat_input.value.strip()
        if room and text:
            dummy_chat_data[state['selected_branch']][room].append(text)
            with message_area:
                ui.label(text).style("margin-bottom: 8px;")
            chat_input.value = ""

    # 버튼에 핸들러 연결
    send_button.on("click", lambda _: send_message())

    # 2) 방 선택 콜백 정의 (이제 chat_input, send_button이 확실히 존재)
    def open_room(room: str):
        state['selected_room'] = room
        chat_title.set_text(f"[{state['selected_branch']}] ▸ [{room}]")
        message_area.clear()
        # 기존 메시지 렌더링
        for msg in dummy_chat_data[state['selected_branch']][room]:
            with message_area:
                ui.label(msg).style("margin-bottom: 8px;")
        # 입력창과 전송 버튼 활성화
        chat_input.enable()
        send_button.enable()

    # 3) 전체 레이아웃
    with ui.row().style("height: 100vh; width: 100vw;"):

        # 왼쪽 사이드
        with ui.column().style("width: 250px; padding: 20px; border-right: 1px solid #ccc;"):
            ui.button("🏠 홈으로", on_click=lambda: ui.navigate.to("/")) \
                .style("margin-bottom: 20px; width: 100%;")

            ui.label(repo_name).style("font-size: 22px; font-weight: bold; margin-bottom: 10px;")

            # 브랜치 전환
            def set_branch(branch: str):
                state['selected_branch'] = branch
                state['selected_room'] = None
                ui.navigate.to(f'/project/{repo_name}')

            for branch in dummy_chat_data.keys():
                color = 'red' if state['selected_branch'] == branch else 'grey'
                ui.button(branch.upper(), on_click=lambda b=branch: set_branch(b)) \
                    .props(f"flat color={color}") \
                    .style("width: 100%; font-weight: bold; margin-bottom: 10px;")

            ui.separator()
            ui.label("채팅방 목록").style("margin-top: 10px; font-weight: bold;")

            # 채팅방 목록 버튼
            for room in dummy_chat_data[state['selected_branch']].keys():
                ui.button(room, on_click=lambda r=room: open_room(r)) \
                    .style("width: 100%; margin: 5px 0;")

            # 새 채팅방 생성
            def create_room():
                with ui.dialog() as dialog, ui.card():
                    ui.label("새 채팅방 생성")
                    new_room = ui.input("채팅방 제목")

                    def add_room():
                        dummy_chat_data[state['selected_branch']][new_room.value] = []
                        ui.notify(f"{new_room.value} 생성됨")
                        dialog.close()
                        ui.navigate.to(f"/project/{repo_name}")

                    ui.button("생성", on_click=add_room)
                    ui.button("닫기", on_click=dialog.close)
                dialog.open()

            ui.button("채팅방 생성", on_click=create_room) \
                .style("margin-top: 20px;")

        # 오른쪽 메인 영역: 제목, 메시지, 입력창+버튼
        with ui.column().style("flex: 1; padding: 20px;"):
            chat_title
            message_area
            with ui.row():
                chat_input
                send_button
