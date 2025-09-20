from nicegui import ui
from src.components.header import Header
from src.data.dummy_data import DummyDataService

class RepositorySettingsPage:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.data_service = DummyDataService()
        repositories = self.data_service.get_repositories()
        self.selected_repo = repositories[0] if repositories else None

    def render(self):
        with ui.column().style('width: 100%; min-height: 100vh; margin: 0; padding: 0;'):
            Header(self.auth_service).render()

            with ui.row().style('width: 100%; height: calc(100vh - 60px); margin: 0; padding: 0;'):
                self.render_sidebar()
                self.render_main_content()

    def render_sidebar(self):
        with ui.column().style('width: 320px; height: 100%; background-color: #f8fafc; border-right: 1px solid #e2e8f0; padding: 24px; overflow-y: auto;'):
            ui.html('<h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px;">Repositories</h2>')

            if self.auth_service.is_admin():
                ui.button('➕ Add New Repository', on_click=self.show_add_repository_dialog).style('width: 100%; background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; border: none; margin-bottom: 16px;')

            repositories = self.data_service.get_repositories()

            for repo in repositories:
                self.render_repository_item(repo)

    def render_repository_item(self, repo):
        is_selected = self.selected_repo and self.selected_repo["id"] == repo["id"]

        item_style = 'width: 100%; padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 1px solid transparent;'
        if is_selected:
            item_style += ' background-color: #dbeafe; border-color: #93c5fd;'
        else:
            item_style += ' background-color: white; hover: background-color: #f1f5f9;'

        with ui.column().style(item_style).on('click', lambda r=repo: self.select_repository(r)):
            ui.html(f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;"><span style="color: #2563eb; font-size: 18px;">📁</span><span style="font-weight: 600;">{repo["name"]}</span></div>')
            ui.html(f'<div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">{repo["description"]}</div>')
            ui.html(f'<div style="font-size: 12px; color: #9ca3af;">⭐ {repo["stars"]} • {repo["language"]}</div>')

    def render_main_content(self):
        self.main_content_container = ui.column().style('flex: 1; height: 100%; padding: 24px; overflow-y: auto; background-color: white;')
        with self.main_content_container:
            if not self.selected_repo:
                self.render_empty_state()
            else:
                self.render_repository_details()

    def render_empty_state(self):
        with ui.column().style('width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; text-align: center;'):
            ui.html('<span style="font-size: 72px; color: #9ca3af;">📂</span>')
            ui.html('<h3 style="font-size: 20px; font-weight: 600; color: #4b5563; margin: 16px 0 8px 0;">Select a Repository</h3>')
            ui.html('<p style="color: #6b7280;">Choose a repository from the sidebar to view its details and settings</p>')

    def render_repository_details(self):
        repo = self.selected_repo

        with ui.column().style('width: 100%; gap: 24px;'):
            # Header section
            with ui.row().style('width: 100%; display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;'):
                with ui.row().style('display: flex; align-items: center; gap: 12px;'):
                    ui.html('<span style="color: #2563eb; font-size: 32px;">📁</span>')
                    ui.html(f'<h2 style="font-size: 24px; font-weight: 700; margin: 0;">{repo["name"]}</h2>')
                    self.render_status_badge(repo["status"])

                with ui.row().style('display: flex; gap: 8px;'):
                    ui.button('💬 Open Chat', on_click=lambda: ui.navigate.to(f'/chat/{repo["id"]}')).style('background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; border: none;')
                    if self.auth_service.is_admin():
                        ui.button('⚙️ Admin Options', on_click=lambda: ui.navigate.to(f'/admin/repository/{repo["id"]}')).style('background-color: #6b7280; color: white; padding: 8px 16px; border-radius: 6px; border: none;')

            # Content section
            with ui.row().style('width: 100%; gap: 24px;'):
                with ui.column().style('flex: 1; gap: 24px;'):
                    self.render_repository_info()
                    self.render_sync_status()

                with ui.column().style('width: 320px; gap: 24px;'):
                    self.render_quick_actions()
                    self.render_members_preview()

    def render_repository_info(self):
        repo = self.selected_repo
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Repository Information</h3>')

            info_items = [
                ("Owner", repo["owner"]),
                ("URL", repo["url"]),
                ("Language", repo["language"]),
                ("Stars", f'{repo["stars"]:,}'),
                ("Created", repo["created_at"].strftime("%b %d, %Y")),
                ("Last Sync", repo["last_sync"].strftime("%b %d, %Y at %H:%M"))
            ]

            for label, value in info_items:
                with ui.row().style('display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;'):
                    ui.html(f'<span style="font-weight: 500; color: #374151;">{label}</span>')
                    if label == "URL":
                        ui.html(f'<a href="{value}" target="_blank" style="color: #2563eb; text-decoration: none;">{value}</a>')
                    else:
                        ui.html(f'<span style="color: #6b7280;">{value}</span>')

    def render_sync_status(self):
        repo = self.selected_repo
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Synchronization Status</h3>')

            with ui.row().style('display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;'):
                ui.html('<span style="font-weight: 500; color: #374151;">Vector Database</span>')
                self.render_vectordb_status(repo["vectordb_status"])

            with ui.row().style('display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;'):
                ui.html('<span style="font-weight: 500; color: #374151;">Collections</span>')
                ui.html(f'<span style="color: #6b7280;">{repo["collections_count"]} active</span>')

            if self.auth_service.is_admin():
                with ui.row().style('display: flex; gap: 8px; margin-top: 16px;'):
                    ui.button('🔄 Sync Now', on_click=lambda: self.trigger_sync()).style('background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; border: none;')
                    ui.button('📄 View Logs', on_click=lambda: self.show_sync_logs()).style('background-color: #6b7280; color: white; padding: 8px 16px; border-radius: 6px; border: none;')

    def render_quick_actions(self):
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Quick Actions</h3>')

            actions = [
                ("🗄️ View Vector DB", lambda: ui.navigate.to(f'/admin/vectordb/{self.selected_repo["id"]}'))
            ]

            if self.auth_service.is_admin():
                actions.extend([
                    ("⚙️ Repository Options", lambda: ui.navigate.to(f'/admin/repository/{self.selected_repo["id"]}')),
                    ("👥 Manage Members", lambda: self.show_members_dialog())
                ])

            for label, action in actions:
                ui.button(label, on_click=action).style('width: 100%; text-align: left; background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;')

    def render_members_preview(self):
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            with ui.row().style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;'):
                ui.html('<h3 style="font-size: 18px; font-weight: 600;">Members</h3>')
                if self.auth_service.is_admin():
                    ui.button('👥 Manage', on_click=self.show_members_dialog).style('background-color: #6b7280; color: white; padding: 4px 8px; border-radius: 4px; border: none; font-size: 12px;')

            members = self.data_service.get_repository_members(self.selected_repo["id"])[:3]

            for member in members:
                with ui.row().style('display: flex; align-items: center; gap: 12px; margin-bottom: 12px;'):
                    ui.html('<div style="width: 32px; height: 32px; background-color: #dbeafe; color: #2563eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;">👤</div>')
                    ui.html(f'<div><div style="font-weight: 500;">{member["username"]}</div><div style="font-size: 12px; color: #6b7280;">{member["role"]}</div></div>')

            if len(self.data_service.get_repository_members(self.selected_repo["id"])) > 3:
                ui.html(f'<div style="text-align: center; font-size: 12px; color: #6b7280;">... and {len(self.data_service.get_repository_members(self.selected_repo["id"])) - 3} more</div>')

    def render_status_badge(self, status):
        colors = {
            'active': 'bg-green-100 text-green-800',
            'syncing': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-3 py-1 rounded-full text-sm {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def render_vectordb_status(self, status):
        colors = {
            'healthy': 'bg-green-100 text-green-800',
            'syncing': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-2 py-1 rounded-full text-xs {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def select_repository(self, repo):
        self.selected_repo = repo
        # Update the main content area
        self.main_content_container.clear()
        with self.main_content_container:
            if not self.selected_repo:
                self.render_empty_state()
            else:
                self.render_repository_details()

    def show_add_repository_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Add New Repository</h3>')

            with ui.column().classes('gap-4'):
                repo_url = ui.input('Repository URL', placeholder='https://github.com/owner/repo').classes('rag-input w-full')
                description = ui.textarea('Description', placeholder='Optional description').classes('rag-input w-full')

                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary')
                    ui.button('Add Repository', on_click=lambda: self.add_repository(repo_url.value, description.value, dialog)).classes('rag-button-primary')

        dialog.open()

    def add_repository(self, url, description, dialog):
        if not url:
            ui.notify('Please enter a repository URL', color='red')
            return

        ui.notify('Repository added successfully!', color='green')
        dialog.close()

    def show_members_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Repository Members</h3>')

            members = self.data_service.get_repository_members(self.selected_repo["id"])

            with ui.column().classes('gap-3 max-h-80 overflow-y-auto'):
                for member in members:
                    with ui.row().classes('items-center justify-between p-3 border rounded-lg'):
                        with ui.row().classes('items-center gap-3'):
                            ui.html('<div class="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm">👤</div>')
                            with ui.column():
                                ui.label(member["username"]).classes('font-medium')
                                ui.label(member["email"]).classes('text-sm text-gray-500')
                        ui.label(member["role"]).classes('text-sm px-2 py-1 bg-gray-100 rounded')

            ui.button('Close', on_click=dialog.close).classes('rag-button-secondary w-full mt-4')

        dialog.open()

    def trigger_sync(self):
        ui.notify('Synchronization started...', color='blue')

    def show_sync_logs(self):
        ui.notify('Sync logs feature coming soon', color='blue')