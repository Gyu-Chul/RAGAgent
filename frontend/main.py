from nicegui import ui
from pages import home


# 메인 페이지 라우팅
@ui.page('/')
def home_page():
    home.render()

ui.run(title="GitAI", reload=True)
