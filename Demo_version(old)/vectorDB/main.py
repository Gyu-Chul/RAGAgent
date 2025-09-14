from nicegui import ui
from src.pages.home import render_home
from src.pages.vector_db import render_vector_db

@ui.page('/')
def home_page():
    render_home()


@ui.page('/vector')
def vector_db_page():
    render_vector_db()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='GitAI', reload=True)
