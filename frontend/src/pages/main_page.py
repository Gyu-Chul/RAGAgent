from nicegui import ui
from src.components.header import Header
from src.services.api_service import api_service

class MainPage:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.api_service = api_service

    def render(self):
        with ui.column().classes('w-full min-h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1 p-6 gap-6'):
                with ui.column().classes('flex-1 gap-6'):
                    self.render_repositories_section()

                with ui.column().classes('w-80 gap-6'):
                    self.render_quick_stats()
                    self.render_recent_activity()


    def render_repositories_section(self):
        with ui.card().classes('rag-card w-full'):
            with ui.column().classes('gap-4'):
                ui.html('<h3 class="text-xl font-semibold">Your Repositories</h3>')

                try:
                    repositories = self.api_service.get_repositories()[:3]
                except Exception as e:
                    ui.notify(f"Failed to load repositories: {str(e)}", type='negative')
                    repositories = []

                with ui.grid(columns=1).classes('w-full gap-4'):
                    for repo in repositories:
                        self.render_repository_card(repo)

    def render_repository_card(self, repo):
        with ui.card().classes('border hover:shadow-lg transition-all p-4'):
            with ui.row().classes('w-full items-start justify-between'):
                with ui.column().classes('flex-1 gap-2'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html('<span style="color: #2563eb; font-size: 18px;">📁</span>')
                        ui.html(f'<h4 class="font-semibold">{repo["name"]}</h4>')
                        self.render_status_badge(repo["status"])

                    ui.html(f'<p class="text-sm text-gray-600">{repo["description"]}</p>')

                    with ui.row().classes('items-center gap-4 text-sm text-gray-500'):
                        ui.html(f'<span>⭐ {repo["stars"]}</span>')
                        ui.html(f'<span>👥 {repo["members_count"]} members</span>')
                        ui.html(f'<span>🗄️ {repo["collections_count"]} collections</span>')

                with ui.column().classes('gap-2'):
                    ui.button('💬 Chat', on_click=lambda repo_id=repo["id"]: ui.navigate.to(f'/chat/{repo_id}')).classes('rag-button-primary text-xs')
                    if self.auth_service.is_admin():
                        ui.button('⚙️ Manage', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-secondary text-xs')

    def render_status_badge(self, status):
        colors = {
            'active': 'bg-green-100 text-green-800',
            'syncing': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-2 py-1 rounded-full text-xs {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def render_quick_stats(self):
        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Quick Stats</h3>')

            user = self.auth_service.get_current_user()
            user_email = user["email"] if user else "unknown@ragit.com"

            stats = [
                {"label": "Total Repositories", "value": "3", "emoji": "📁"},
                {"label": "Active Chats", "value": str(self.api_service.get_user_active_chats_count(user_email)), "emoji": "💬"},
                {"label": "Vector Collections", "value": "8", "emoji": "🗄️"},
                {"label": "Total Embeddings", "value": "1.9K", "emoji": "🧠"}
            ]

            with ui.column().classes('gap-3'):
                for stat in stats:
                    with ui.row().classes('items-center justify-between p-3 bg-gray-50 rounded-lg'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(f'<span class="text-blue-600 text-lg">{stat["emoji"]}</span>')
                            ui.label(stat["label"]).classes('text-sm')
                        ui.label(stat["value"]).classes('font-semibold text-lg')

    def render_recent_activity(self):
        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Recent Activity</h3>')

            user = self.auth_service.get_current_user()
            user_email = user["email"] if user else "unknown@ragit.com"
            try:
                activities = self.api_service.get_user_recent_activity(user_email)
            except Exception as e:
                ui.notify(f"Failed to load recent activity: {str(e)}", type='negative')
                activities = []

            emojis = {
                "chat": "💬",
                "sync": "🔄",
                "member": "👤",
                "collection": "🗄️"
            }

            with ui.column().classes('gap-3'):
                for activity in activities:
                    with ui.row().classes('items-start gap-3 p-2'):
                        ui.html(f'<span class="text-gray-500 mt-1">{emojis[activity["type"]]}</span>')
                        with ui.column().classes('flex-1 gap-1'):
                            ui.label(activity["message"]).classes('text-sm')
                            ui.label(activity["time"]).classes('text-xs text-gray-500')

    def show_admin_menu(self):
        with ui.dialog() as dialog, ui.card():
            ui.html('<h3 class="text-lg font-semibold mb-4">Admin Panel</h3>')

            with ui.column().classes('gap-3'):
                ui.button('📁 Repository Management', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-primary w-full')
                ui.button('👥 User Management', on_click=lambda: ui.notify('Feature coming soon')).classes('rag-button-secondary w-full')
                ui.button('📄 System Logs', on_click=lambda: ui.notify('Feature coming soon')).classes('rag-button-secondary w-full')
                ui.button('⚙️ Settings', on_click=lambda: ui.notify('Feature coming soon')).classes('rag-button-secondary w-full')

            ui.button('Close', on_click=dialog.close).classes('rag-button-secondary w-full mt-4')

        dialog.open()