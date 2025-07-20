from nicegui import ui
from src.pages.main_page.home import render_home
from src.pages.repository_page.repository_page  import render_repository_page
from src.pages.sample.sample import render_sample_page
from src.pages.vector_db.vector_db import render_vector_db

@ui.page('/')
def home_page():
    render_home()

@ui.page('/project/{repo_name}')
def repository_page(repo_name: str):
    render_repository_page(repo_name)

@ui.page('/sample')
def sample_page():
    render_sample_page()

@ui.page('/project/{repo_name}/vectordb')
def vector_db_page(repo_name: str):
    render_vector_db(repo_name) # repo_name을 인자로 전달

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GitAI', reload=True)