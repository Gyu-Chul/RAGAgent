# src/components/sidebar.py

from nicegui import ui
from src.services.data_service import load_chat_data

data = load_chat_data()
state = {'branch': next(iter(data)), 'room': None}

def sidebar(repo_name: str, on_room_open, on_branch_change):
    with ui.column().style('width:260px; padding:20px; border-right:1px solid #ccc;'):
        # 홈으로 버튼
        ui.button('🏠 홈으로', on_click=lambda: ui.navigate.to('/')) \
          .style('margin-bottom:20px; width:100%;')

        # 레포 이름
        ui.label(repo_name) \
          .style('font-size:22px; font-weight:bold; margin-bottom:10px;')

        # 브랜치 버튼
        for br in data:
            color = 'red' if state['branch'] == br else 'grey'
            ui.button(br.upper(), on_click=lambda b=br: on_branch_change(b)) \
              .props(f'flat color={color}') \
              .style('width:100%; font-weight:bold; margin-bottom:10px;')

        ui.separator()

        # 채팅방 목록
        ui.label('채팅방 목록') \
          .style('font-weight:bold; margin-top:10px;')
        for room in data[state['branch']]:
            ui.button(room, on_click=lambda r=room: on_room_open(r)) \
              .style('width:100%; margin:5px 0;')

        # 새 채팅방 생성 버튼
        ui.button('채팅방 생성', on_click=lambda: None) \
          .style('margin-top:20px; width:100%;')
