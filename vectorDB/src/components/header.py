from nicegui import ui

def logo_header():
    with ui.row().style('align-items:center; margin-bottom:40px;'):
        ui.label('GitAI - vectorDB').style('font-size:28px; font-weight:bold;')