from nicegui import ui
from frontend.src.components.header import Header
from frontend.src.services.api_service import APIService

class RepositoryOptionsPage:
    def __init__(self, repo_id: str, auth_service):
        self.repo_id = repo_id
        self.auth_service = auth_service
        self.api_service = APIService(auth_service=auth_service)
        try:
            self.repository = self.api_service.get_repository(repo_id)
        except Exception as e:
            ui.notify(f"Failed to load repository: {str(e)}", type='negative')
            self.repository = None

    def render(self):
        if not self.repository:
            return self.render_not_found()

        with ui.column().classes('w-full min-h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1'):
                self.render_sidebar()
                self.render_main_content()

    def render_not_found(self):
        with ui.column().classes('w-full min-h-screen items-center justify-center'):
            ui.html('<h2 class="text-2xl font-bold text-gray-600">Repository Not Found</h2>')
            ui.button('Back to Repositories', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-primary mt-4')

    def render_sidebar(self):
        with ui.column().classes('rag-sidebar w-80 p-6 gap-4'):
            with ui.row().classes('items-center gap-3 mb-4'):
                ui.icon('folder').classes('text-blue-600 text-xl')
                ui.html(f'<h2 class="text-lg font-semibold">{self.repository["name"]}</h2>')

            navigation_items = [
                ("Members", "people", "members"),
                ("Sync Settings", "sync", "sync"),
                ("Vector Database", "storage", "vectordb"),
                ("Repository Logs", "article", "logs"),
                ("Danger Zone", "warning", "danger")
            ]

            with ui.column().classes('gap-2'):
                for label, icon, section in navigation_items:
                    ui.button(label, icon=icon, on_click=lambda s=section: self.scroll_to_section(s)).classes('rag-button-secondary w-full text-left justify-start')

            ui.separator().classes('my-4')

            ui.button('Back to Repositories', icon='arrow_back', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-secondary w-full')

    def render_main_content(self):
        with ui.column().classes('flex-1 p-6 gap-8'):
            self.render_header_section()
            self.render_members_section()
            self.render_sync_section()
            self.render_vectordb_section()
            self.render_logs_section()
            self.render_danger_section()

    def render_header_section(self):
        repo = self.repository
        with ui.card().classes('rag-card'):
            with ui.row().classes('w-full items-start justify-between'):
                with ui.column().classes('flex-1 gap-2'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('folder').classes('text-blue-600 text-2xl')
                        ui.html(f'<h1 class="text-2xl font-bold">{repo["name"]}</h1>')
                        self.render_status_badge(repo["status"])

                    ui.html(f'<p class="text-gray-600">{repo.get("description", "")}</p>')

                    with ui.row().classes('items-center gap-4 text-sm text-gray-500 mt-2'):
                        ui.html(f'<span>📄 {repo.get("file_count", 0)} files</span>')
                        ui.html(f'<span>🗄️ {repo.get("collections_count", 0)} collections</span>')

                with ui.column().classes('gap-2'):
                    ui.button('Open Chat', icon='chat', on_click=lambda: ui.navigate.to(f'/chat/{repo["id"]}')).classes('rag-button-primary')
                    ui.button('View Vector DB', icon='storage', on_click=lambda: ui.navigate.to(f'/admin/vectordb/{repo["id"]}')).classes('rag-button-secondary')

    def render_members_section(self):
        with ui.card().classes('rag-card').props('id=members'):
            with ui.row().classes('items-center justify-between mb-4'):
                ui.html('<h3 class="text-lg font-semibold">Member Management</h3>')
                ui.button('Add Member', icon='person_add', on_click=self.show_add_member_dialog).classes('rag-button-primary')

            try:
                members = self.api_service.get_repository_members(self.repo_id)
            except Exception as e:
                ui.notify(f"Failed to load members: {str(e)}", type='negative')
                members = []

            with ui.column().classes('gap-3'):
                for member in members:
                    with ui.card().classes('border p-4'):
                        with ui.row().classes('items-center justify-between'):
                            with ui.row().classes('items-center gap-3 flex-1'):
                                ui.html('<div class="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm">👤</div>')
                                with ui.column().classes('flex-1'):
                                    ui.label(member.get("username", "Unknown")).classes('font-medium')
                                    ui.label(member.get("email", "")).classes('text-sm text-gray-500')
                                    joined_at = member.get("joined_at")
                                    if joined_at:
                                        ui.label(f'Joined {joined_at.strftime("%b %d, %Y")}').classes('text-xs text-gray-400')

                            with ui.row().classes('items-center gap-3'):
                                role_options = ['admin', 'member', 'viewer']
                                ui.select(role_options, value=member.get("role", "member"), on_change=lambda e, m=member: self.update_member_role(m, e.value)).classes('min-w-32')
                                ui.button(icon='delete', on_click=lambda m=member: self.remove_member(m)).classes('bg-red-100 text-red-600 hover:bg-red-200')

    def render_sync_section(self):
        with ui.card().classes('rag-card').props('id=sync'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Synchronization Settings</h3>')

            repo = self.repository

            with ui.column().classes('gap-6'):
                with ui.row().classes('items-center justify-between p-4 bg-gray-50 rounded-lg'):
                    with ui.column():
                        ui.label('Auto Sync').classes('font-medium')
                        ui.label('Automatically sync repository changes').classes('text-sm text-gray-600')
                    ui.switch(value=True, on_change=lambda e: ui.notify(f'Auto sync {"enabled" if e.value else "disabled"}')).classes('ml-4')

                with ui.row().classes('items-center justify-between p-4 bg-gray-50 rounded-lg'):
                    with ui.column():
                        ui.label('Sync Frequency').classes('font-medium')
                        ui.label('How often to check for updates').classes('text-sm text-gray-600')
                    ui.select(['Every hour', 'Every 6 hours', 'Daily', 'Weekly'], value='Every 6 hours').classes('min-w-40')

                with ui.column().classes('gap-3'):
                    ui.label('Current Status').classes('font-medium')
                    with ui.row().classes('items-center gap-3'):
                        ui.label(f'Last sync: {repo["last_sync"].strftime("%b %d, %Y at %H:%M")}')
                        self.render_sync_status(repo["vectordb_status"])

                    with ui.row().classes('gap-2'):
                        ui.button('Sync Now', icon='sync', on_click=self.trigger_sync).classes('rag-button-primary')
                        ui.button('Force Full Sync', icon='refresh', on_click=self.force_full_sync).classes('rag-button-secondary')

    def render_vectordb_section(self):
        with ui.card().classes('rag-card').props('id=vectordb'):
            with ui.row().classes('items-center justify-between mb-4'):
                ui.html('<h3 class="text-lg font-semibold">Vector Database Management</h3>')
                ui.button('Manage Collections', icon='storage', on_click=lambda: ui.navigate.to(f'/admin/vectordb/{self.repo_id}')).classes('rag-button-primary')

            collections = self.api_service.get_vectordb_collections(self.repo_id)

            with ui.column().classes('gap-3'):
                for collection in collections:
                    with ui.card().classes('border p-4'):
                        with ui.row().classes('items-center justify-between'):
                            with ui.column().classes('flex-1'):
                                ui.label(collection["name"]).classes('font-medium')
                                ui.label(collection["description"]).classes('text-sm text-gray-600')
                                with ui.row().classes('items-center gap-4 text-xs text-gray-500 mt-1'):
                                    ui.label(f'{collection["entity_count"]:,} entities')
                                    ui.label(f'Dimension: {collection["dimension"]}')
                                    ui.label(f'Index: {collection["index_type"]}')

                            with ui.row().classes('items-center gap-2'):
                                self.render_collection_status(collection["status"])
                                ui.button(icon='more_vert', on_click=lambda c=collection: self.show_collection_options(c)).classes('text-gray-400')

    def render_logs_section(self):
        with ui.card().classes('rag-card').props('id=logs'):
            with ui.row().classes('items-center justify-between mb-4'):
                ui.html('<h3 class="text-lg font-semibold">Repository Logs</h3>')
                ui.button('Export Logs', icon='download', on_click=self.export_logs).classes('rag-button-secondary')

            log_entries = [
                {"time": "2024-01-15 14:30", "type": "sync", "message": "Repository synchronized successfully"},
                {"time": "2024-01-15 14:25", "type": "member", "message": "New member 'developer1' added"},
                {"time": "2024-01-15 14:20", "type": "vectordb", "message": "Vector embeddings updated"},
                {"time": "2024-01-15 14:15", "type": "error", "message": "Failed to sync branch 'feature/new-ui'"},
                {"time": "2024-01-15 14:10", "type": "sync", "message": "Automatic sync initiated"}
            ]

            with ui.column().classes('gap-2 max-h-80 overflow-y-auto'):
                for entry in log_entries:
                    with ui.row().classes('items-center gap-3 p-3 border-b'):
                        self.render_log_icon(entry["type"])
                        with ui.column().classes('flex-1'):
                            ui.label(entry["message"]).classes('text-sm')
                            ui.label(entry["time"]).classes('text-xs text-gray-500')

    def render_danger_section(self):
        with ui.card().classes('rag-card border-red-200').props('id=danger'):
            ui.html('<h3 class="text-lg font-semibold text-red-600 mb-4">Danger Zone</h3>')
            ui.html('<p class="text-sm text-gray-600 mb-4">These actions are irreversible and will permanently affect the repository.</p>')

            danger_actions = [
                ("Clear Vector Database", "Delete all vector embeddings and collections", self.clear_vectordb),
                ("Reset Repository", "Remove all data and start fresh", self.reset_repository),
                ("Delete Repository", "Permanently remove repository from RAGIT", self.delete_repository)
            ]

            with ui.column().classes('gap-3'):
                for title, description, action in danger_actions:
                    with ui.card().classes('border border-red-200 p-4'):
                        with ui.row().classes('items-center justify-between'):
                            with ui.column():
                                ui.label(title).classes('font-medium text-red-600')
                                ui.label(description).classes('text-sm text-gray-600')
                            ui.button(title, icon='warning', on_click=action).classes('bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700')

    def render_status_badge(self, status):
        colors = {
            'active': 'bg-green-100 text-green-800',
            'syncing': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-3 py-1 rounded-full text-sm {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def render_sync_status(self, status):
        colors = {
            'healthy': 'bg-green-100 text-green-800',
            'syncing': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-2 py-1 rounded-full text-xs {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def render_collection_status(self, status):
        colors = {
            'ready': 'bg-green-100 text-green-800',
            'building': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-2 py-1 rounded-full text-xs {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def render_log_icon(self, log_type):
        icons = {
            'sync': ('sync', 'text-blue-600'),
            'member': ('person_add', 'text-green-600'),
            'vectordb': ('storage', 'text-purple-600'),
            'error': ('error', 'text-red-600')
        }
        icon, color = icons.get(log_type, ('info', 'text-gray-600'))
        ui.icon(icon).classes(f'{color}')

    def scroll_to_section(self, section):
        ui.run_javascript(f'document.getElementById("{section}").scrollIntoView({{behavior: "smooth"}})')

    def show_add_member_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Add Member</h3>')

            with ui.column().classes('gap-4'):
                email_input = ui.input('Email', placeholder='member@example.com').classes('rag-input w-full')
                role_select = ui.select(['member', 'admin', 'viewer'], value='member', label='Role').classes('w-full')

                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary')
                    ui.button('Add Member', on_click=lambda: self.add_member(email_input.value, role_select.value, dialog)).classes('rag-button-primary')

        dialog.open()

    def add_member(self, email, role, dialog):
        if not email:
            ui.notify('Please enter an email address', color='red')
            return

        try:
            # 1. 이메일로 사용자 검색
            user = self.api_service.search_user_by_email(email)

            # 2. 사용자 ID로 멤버 추가
            self.api_service.add_repository_member(self.repo_id, user["id"], role)
            ui.notify(f'Member {email} added with role {role}', color='green')
            dialog.close()
            # 페이지 새로고침으로 멤버 목록 업데이트
            ui.navigate.reload()
        except Exception as e:
            ui.notify(f'Failed to add member: {str(e)}', color='red')

    def update_member_role(self, member, new_role):
        try:
            self.api_service.update_member_role(self.repo_id, member["id"], new_role)
            ui.notify(f'{member.get("username", "Member")} role updated to {new_role}', color='green')
        except Exception as e:
            ui.notify(f'Failed to update role: {str(e)}', color='red')

    def remove_member(self, member):
        try:
            success = self.api_service.remove_repository_member(self.repo_id, member["id"])
            if success:
                ui.notify(f'{member.get("username", "Member")} removed from repository', color='green')
                ui.navigate.reload()
            else:
                ui.notify('Failed to remove member', color='red')
        except Exception as e:
            ui.notify(f'Failed to remove member: {str(e)}', color='red')

    def trigger_sync(self):
        ui.notify('Synchronization started...', color='blue')

    def force_full_sync(self):
        ui.notify('Full synchronization started...', color='blue')

    def show_collection_options(self, collection):
        ui.notify(f'Collection options for {collection["name"]}', color='blue')

    def export_logs(self):
        ui.notify('Logs will be exported to your email', color='blue')

    def clear_vectordb(self):
        ui.notify('Vector database clearing is not available in demo mode', color='blue')

    def reset_repository(self):
        ui.notify('Repository reset is not available in demo mode', color='blue')

    def delete_repository(self):
        ui.notify('Repository deletion is not available in demo mode', color='blue')