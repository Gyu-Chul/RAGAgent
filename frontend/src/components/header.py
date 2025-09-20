from nicegui import ui

class Header:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def render(self):
        with ui.row().classes('rag-header w-full items-center justify-between'):
            with ui.row().classes('items-center gap-4'):
                ui.button('🤖 RAG-AGENT', on_click=lambda: ui.navigate.to('/main')).style('color: white; background: transparent; border: none; font-size: 24px; font-weight: 700; padding: 8px; cursor: pointer;')

            with ui.row().classes('items-center gap-4'):
                user = self.auth_service.get_current_user()
                if user:
                    ui.label(f"Welcome, {user['name']}").classes('text-white')

                    with ui.row().classes('items-center gap-2'):
                        ui.button('👤 Profile', on_click=lambda: ui.navigate.to('/account')).style('color: white; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px;')
                        ui.button('📁 Repositories', on_click=lambda: ui.navigate.to('/repositories')).style('color: white; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px;')
                        if self.auth_service.is_admin():
                            ui.button('⚙️ Admin', on_click=lambda: ui.navigate.to('/repositories')).style('color: white; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px;')
                        ui.button('🚪 Logout', on_click=self.handle_logout).style('color: white; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px;')

    def handle_logout(self):
        self.auth_service.logout()
        ui.notify('Logged out successfully', color='green')
        ui.navigate.to('/login')