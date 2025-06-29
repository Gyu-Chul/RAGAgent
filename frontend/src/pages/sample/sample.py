from nicegui import ui
from src.components.sample.http_call_button import http_call_button

def render_sample_page():
    with ui.column().classes('w-full items-center'):
        ui.label('샘플 페이지').classes('text-h4 font-bold mb-4')
        http_call_button()