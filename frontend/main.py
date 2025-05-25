from nicegui import ui
from src.pages.home import render_home
from src.pages.project import render_project

@ui.page('/')
def home_page():
    render_home()

@ui.page('/project/{name}')
def project_page(name: str):
    render_project(name)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GitAI', reload=True)