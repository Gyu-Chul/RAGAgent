from nicegui import ui
from frontend.src.components.header import Header
from frontend.src.services.api_service import APIService

class MainPage:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.api_service = APIService(auth_service=auth_service)

    def render(self):
        with ui.column().classes('w-full min-h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1 p-6 gap-6'):
                with ui.column().classes('flex-1 gap-6'):
                    self.render_repositories_section()

                with ui.column().classes('w-80 gap-6'):
                    self.render_quick_stats()


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

                    ui.html(f'<p class="text-sm text-gray-600">{repo.get("description", "")}</p>')

                    with ui.row().classes('items-center gap-4 text-sm text-gray-500'):
                        ui.html(f'<span>📄 {repo.get("file_count", 0)} files</span>')
                        ui.html(f'<span>🗄️ {repo.get("collections_count", 0)} collections</span>')

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

            # 실제 데이터 가져오기
            try:
                repositories = self.api_service.get_repositories()
                total_repos = len(repositories)

                # 전체 파일 개수 계산
                total_files = sum(repo.get("file_count", 0) for repo in repositories)

                # 전체 컬렉션 개수 계산
                total_collections = sum(repo.get("collections_count", 0) for repo in repositories)

            except Exception as e:
                total_repos = 0
                total_files = 0
                total_collections = 0

            stats = [
                {"label": "Total Repositories", "value": str(total_repos), "emoji": "📁"},
                {"label": "Total Files", "value": str(total_files), "emoji": "📄"},
                {"label": "Vector Collections", "value": str(total_collections), "emoji": "🗄️"}
            ]

            with ui.column().classes('gap-3'):
                for stat in stats:
                    with ui.row().classes('items-center justify-between p-3 bg-gray-50 rounded-lg'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(f'<span class="text-blue-600 text-lg">{stat["emoji"]}</span>')
                            ui.label(stat["label"]).classes('text-sm')
                        ui.label(stat["value"]).classes('font-semibold text-lg')

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