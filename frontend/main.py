from nicegui import ui
from src.pages.main_page.home import render_home
from src.pages.repository_page.repository_page  import render_repository_page
from src.pages.sample.sample import render_sample_page

@ui.page('/')
def home_page():
    render_home()

@ui.page('/project/{repo_name}')
def repository_page(repo_name: str):
    render_repository_page(repo_name)

@ui.page('/sample')
def sample_page():
    render_sample_page()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GitAI', reload=True)