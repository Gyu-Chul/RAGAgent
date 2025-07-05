from nicegui import ui
from src.pages.main_page.home import render_home
from src.pages.project import render_project
from src.pages.sample.sample import render_sample_page

@ui.page('/')
def home_page():
    render_home()

@ui.page('/project/{name}')
def project_page(name: str):
    render_project(name)

@ui.page('/sample')
def sample_page():
    render_sample_page()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GitAI', reload=True)