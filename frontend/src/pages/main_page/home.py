# src/pages/home.py

from nicegui import ui
from functools import partial
from src.components.main_page.api import gitclone
import os


current_file_path = os.path.abspath(__file__)

#직관적인 경로체크 코드 수정 필요
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))))
parsed_repo_path = os.path.join(project_root, 'git-agent3', 'parsed_repository')

def logo_header():
    with ui.row().style('align-items:center; margin-bottom:40px;'):
        ui.label('GitAI').style('font-size:28px; font-weight:bold;')

def connect_repo():
    with ui.dialog() as dialog, ui.card():
        ui.label('새 레포지토리 연결').style('font-weight:bold; font-size:18px;')
        repo_input = ui.input('Git 레포지토리 링크')

        gitcloen_handler = partial(gitclone, repo_input)

        ui.button('연결', on_click=gitcloen_handler)


        ui.button('닫기', on_click=dialog.close)
    dialog.open()



def render_home():
    with ui.row().style('height:100vh; width:100vw; justify-content:center; align-items:center;'):
        with ui.column().style('align-items:center; padding:30px; border:2px solid #ccc; border-radius:15px; box-shadow:0 0 10px #ccc; min-width:350px;'):
            # 로고 & 타이틀ㄴ
            logo_header()

            parsed_repo = []
            if os.path.exists(parsed_repo_path) and os.path.isdir(parsed_repo_path):
                parsed_repo = [name for name in os.listdir(parsed_repo_path) if
                               os.path.isdir(os.path.join(parsed_repo_path, name))]

            print(parsed_repo)
            if parsed_repo:
                ui.label('연결된 레포지토리').style('font-size:22px; font-weight:bold; margin-bottom:20px;')
            else:
                ui.label('연결된 레포지토리가 존재하지 않습니다.').style('font-size:22px; font-weight:bold; margin-bottom:20px;')

            # 더미 레포 버튼
            for repo in parsed_repo:
                ui.button(repo.upper(), on_click=lambda r=repo: ui.navigate.to(f'/project/{r}')).style('width:250px; height:50px; margin:10px; font-size:16px;')

            # NEW CONNECT 버튼
            ui.button('NEW CONNECT', on_click=connect_repo).props('outline color=blue').style('width:250px; height:50px; margin-top:30px; font-size:16px;')
