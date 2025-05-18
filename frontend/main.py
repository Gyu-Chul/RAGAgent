from nicegui import ui
from pages import home
from pages import repo_detail

# 메인 페이지 라우팅
@ui.page('/')
def home_page():
    home.render()

@ui.page('/project/{name}')
def repo_page(name: str):
    repo_detail.render(name)

ui.run(title="GitAI", reload=True)
