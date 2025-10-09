"""
RAGIT Frontend Main Application
"""

import logging
from pathlib import Path
from typing import Any
from nicegui import ui, app

# 프론트엔드 로깅 설정
def setup_logging() -> None:
    """프론트엔드 프로세스 자체 로그 캡처를 위한 설정"""
    from datetime import datetime

    # 현재 날짜로 디렉토리 생성
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs") / today
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로그 파일 경로
    log_file = log_dir / f"frontend_{datetime.now().strftime('%H-%M-%S')}.log"

    # NiceGUI와 uvicorn 자체 로그를 파일로 리다이렉트
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 기본 포맷 (프로세스 자체 로그 유지)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # 루트 로거에 파일 핸들러 추가 (모든 로그를 파일로)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # NiceGUI 로거에 파일 핸들러 추가
    nicegui_logger = logging.getLogger("nicegui")
    nicegui_logger.addHandler(file_handler)

    # uvicorn 로거에 파일 핸들러 추가 (NiceGUI가 uvicorn 사용)
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.addHandler(file_handler)

# 로깅 초기화
setup_logging()
from frontend.src.services.auth_service import AuthService
from frontend.src.services.navigation_service import NavigationService
from frontend.src.services.api_service import init_api_service
from frontend.src.pages.auth_page import AuthPage
from frontend.src.pages.main_page import MainPage
from frontend.src.pages.repository_settings_page import RepositorySettingsPage
from frontend.src.pages.account_settings_page import AccountSettingsPage
from frontend.src.pages.vectordb_page import VectorDBPage
from frontend.src.pages.chat_page import ChatPage
from frontend.src.utils.theme import setup_theme

# Global service instances to maintain state across pages
auth_service = AuthService()
nav_service = NavigationService()

# Initialize API service with auth_service
init_api_service(auth_service)

@ui.page('/')
def index() -> Any:
    if not auth_service.is_authenticated():
        return AuthPage(auth_service).render()
    else:
        return MainPage(auth_service).render()

@ui.page('/login')
def login() -> Any:
    return AuthPage(auth_service, mode='login').render()

@ui.page('/signup')
def signup() -> Any:
    return AuthPage(auth_service, mode='signup').render()

@ui.page('/main')
def main_page():
    if not auth_service.is_authenticated():
        ui.navigate.to('/login')
        return
    return MainPage(auth_service).render()

@ui.page('/repositories')
def repositories():
    if not auth_service.is_authenticated():
        ui.navigate.to('/login')
        return
    return RepositorySettingsPage(auth_service).render()

@ui.page('/account')
def account():
    if not auth_service.is_authenticated():
        ui.navigate.to('/login')
        return
    return AccountSettingsPage(auth_service).render()

@ui.page('/admin/repository/{repo_id}')
def repository_options(repo_id: str):
    # Redirect to unified repository page
    ui.navigate.to('/repositories')
    return

@ui.page('/admin/vectordb/{repo_id}')
def vectordb_management(repo_id: str):
    if not auth_service.is_authenticated() or not auth_service.is_admin():
        ui.navigate.to('/login')
        return
    return VectorDBPage(repo_id, auth_service).render()

@ui.page('/chat/{repo_id}')
def chat(repo_id: str):
    if not auth_service.is_authenticated():
        ui.navigate.to('/login')
        return
    return ChatPage(repo_id, auth_service).render()

def run_app():
    setup_theme()
    ui.run(
        title="RAGIT",
        favicon="🤖",
        port=8000,
        show=False,
        reload=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    run_app()