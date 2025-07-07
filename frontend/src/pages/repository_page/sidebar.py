# src/pages/repository_page/sidebar.py
from nicegui import ui


def sidebar(repo_name: str, data: dict, current_branch: str, on_room_open, on_branch_change, on_create_room_click):
    with ui.column().style('width:260px; padding:20px; border-right:1px solid #ccc;'):
        ui.button('🏠 홈으로', on_click=lambda: ui.navigate.to('/')).style('margin-bottom:20px; width:100%;')
        ui.label(repo_name).style('font-size:22px; font-weight:bold; margin-bottom:10px;')

        if data:
            for br in data:
                color = 'blue' if current_branch == br else 'grey'
                ui.button(br.upper(), on_click=lambda b=br: on_branch_change(b)) \
                    .props(f'flat color={color}').style('width:100%; font-weight:bold; margin-bottom:5px;')

        ui.separator().style('margin: 15px 0;')

        ui.label('채팅방 목록').style('font-weight:bold; margin-top:10px;')
        if current_branch and current_branch in data:
            for room in data[current_branch].keys():
                ui.button(room, on_click=lambda r=room: on_room_open(r)) \
                    .style('width:100%; margin:5px 0; justify-content: flex-start; padding-left: 10px;')
        else:
            ui.label("브랜치를 선택하세요.").style('color: grey;')

        ui.button('채팅방 생성', on_click=on_create_room_click, icon='add').style('margin-top:20px; width:100%;')