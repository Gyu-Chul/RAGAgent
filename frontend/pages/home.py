from nicegui import ui

def render():
    with ui.row().style('height:100vh; width:100vw; justify-content:center; align-items:center;'):
        with ui.column().style('align-items:center; padding:30px; border:2px solid #ccc; border-radius:15px; box-shadow:0 0 10px #ccc; min-width:350px;'):
            # 로고 & 타이틀
            with ui.row().style('align-items:center; margin-bottom:40px;'):
                ui.label('GitAI').style('font-size:28px; font-weight:bold;')

            ui.label('연결된 레포지토리').style('font-size:22px; font-weight:bold; margin-bottom:20px;')

            # 더미 버튼
            for repo in ['hab', 'JEYSport',"TEST"]:
                ui.button(
                    repo.upper(),
                    on_click=lambda r=repo: ui.navigate.to(f'/project/{r}')
                ).style('width:250px; height:50px; margin:10px; font-size:16px;')

            # New Connect
            def connect_repo():
                with ui.dialog() as dialog, ui.card():
                    ui.label('새 레포지토리 연결').style('font-weight:bold; font-size:18px;')
                    inp = ui.input('Git 레포지토리 링크')
                    ui.button('연결 시도', on_click=lambda: ui.notify(f'입력된 주소: {inp.value}'))
                    ui.button('닫기', on_click=dialog.close)
                dialog.open()

            ui.button('NEW CONNECT', on_click=connect_repo)\
              .props('outline color=blue')\
              .style('width:250px; height:50px; margin-top:30px; font-size:16px;')
