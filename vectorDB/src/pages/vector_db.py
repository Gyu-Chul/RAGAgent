from nicegui import ui
from src.components.vector_panel import vector_db_panel

def render_vector_db():
    with ui.row().style('height:100vh; width:100vw;'):
        with ui.column().style('width:260px; padding:20px; border-right:1px solid #ccc;'):
            ui.button('🏠 홈으로', on_click=lambda: ui.navigate.to('/')).style('margin-bottom:20px; width:100%;')
            ui.label('📦 벡터 DB 관리').style('font-size:20px; font-weight:bold;')

        with ui.column().style('flex:1; padding:20px;'):
            vector_db_panel()
