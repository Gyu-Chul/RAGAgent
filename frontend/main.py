from nicegui import ui, app
from src.services.auth_service import AuthService
from src.services.navigation_service import NavigationService
from src.pages.auth_page import AuthPage
from src.pages.main_page import MainPage
from src.pages.repository_settings_page import RepositorySettingsPage
from src.pages.account_settings_page import AccountSettingsPage
from src.pages.repository_options_page import RepositoryOptionsPage
from src.pages.vectordb_page import VectorDBPage
from src.pages.chat_page import ChatPage
from src.utils.theme import setup_theme

# Global service instances to maintain state across pages
auth_service = AuthService()
nav_service = NavigationService()

@ui.page('/')
def index():
    if not auth_service.is_authenticated():
        return AuthPage(auth_service).render()
    else:
        return MainPage(auth_service).render()

@ui.page('/login')
def login():
    return AuthPage(auth_service, mode='login').render()

@ui.page('/signup')
def signup():
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
    if not auth_service.is_authenticated() or not auth_service.is_admin():
        ui.navigate.to('/login')
        return
    return RepositoryOptionsPage(repo_id, auth_service).render()

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
        title="RAG-AGENT",
        favicon="🤖",
        port=8086,
        show=False,
        reload=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    run_app()