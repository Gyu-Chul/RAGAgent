from nicegui import ui
from frontend.src.components.header import Header
from frontend.src.services.api_service import APIService

class RepositorySettingsPage:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.api_service = APIService(auth_service=auth_service)
        self.repo_containers = {}  # UI 컨테이너들을 저장할 딕셔너리
        try:
            repositories = self.api_service.get_repositories()
            self.selected_repo = repositories[0] if repositories else None
        except Exception as e:
            ui.notify(f"Failed to load repositories: {str(e)}", type='negative')
            self.selected_repo = None

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

            try:
                repositories = self.api_service.get_repositories()
            except Exception as e:
                ui.notify(f"Failed to load repositories: {str(e)}", type='negative')
                repositories = []

            for repo in repositories:
                self.render_repository_item(repo)

    def render_repository_item(self, repo):
        is_selected = self.selected_repo and self.selected_repo["id"] == repo["id"]

        if is_selected:
            item_style = 'width: 100%; padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 2px solid #3b82f6; background-color: #dbeafe;'
        else:
            item_style = 'width: 100%; padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 1px solid #e5e7eb; background-color: white;'

        # Create a container that will be refreshed when selection changes
        container = ui.column().style(item_style).on('click', lambda r=repo: self.select_repository(r))

        with container:
            # Repository name과 status badge
            with ui.row().style('display: flex; align-items: center; gap: 8px; margin-bottom: 4px;'):
                ui.html(f'<span style="color: #2563eb; font-size: 18px;">📁</span>')
                ui.html(f'<span style="font-weight: 600;">{repo["name"]}</span>')
                # Status badge
                status = repo.get("status", "active")
                status_colors = {
                    'pending': 'background-color: #fef3c7; color: #92400e;',
                    'syncing': 'background-color: #fef3c7; color: #92400e;',
                    'active': 'background-color: #d1fae5; color: #065f46;',
                    'error': 'background-color: #fee2e2; color: #991b1b;'
                }
                status_style = status_colors.get(status, 'background-color: #e5e7eb; color: #374151;')
                ui.html(f'<span style="{status_style} padding: 2px 8px; border-radius: 9999px; font-size: 10px; font-weight: 600;">{status.upper()}</span>')

            ui.html(f'<div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">{repo.get("description", "")}</div>')

            # File count와 collections count 표시
            file_count = repo.get("file_count", 0)
            collections_count = repo.get("collections_count", 0)
            ui.html(f'<div style="font-size: 12px; color: #9ca3af;">📄 {file_count} files • 🗄️ {collections_count} collections</div>')

        # Store reference for later updates
        self.repo_containers[repo["id"]] = container

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


            # Content section
            with ui.column().style('width: 100%; gap: 24px;'):
                self.render_repository_info()
                self.render_sync_status()
                self.render_quick_actions()

    def render_repository_info(self):
        repo = self.selected_repo
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Repository Information</h3>')

            # owner 정보는 User 객체에서 가져와야 하므로 임시로 owner_id 표시
            owner_display = repo.get("owner", "Unknown")

            # created_at과 last_sync는 datetime 객체일 수도 있고 None일 수도 있음
            created_at = repo.get("created_at")
            last_sync = repo.get("last_sync")

            created_display = created_at.strftime("%b %d, %Y") if created_at else "N/A"
            last_sync_display = last_sync.strftime("%b %d, %Y at %H:%M") if last_sync else "Not synced yet"

            info_items = [
                ("Owner", owner_display),
                ("URL", repo.get("url", "")),
                ("File Count", f'{repo.get("file_count", 0):,}'),
                ("Collections", f'{repo.get("collections_count", 0):,}'),
                ("Created", created_display),
                ("Last Sync", last_sync_display)
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

    def render_quick_actions(self):
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Actions</h3>')

            # Admin actions
            actions = []

            if self.auth_service.is_admin():
                actions.extend([
                    ("👥 Manage Members", lambda: self.show_members_dialog()),
                    ("🗑️ Delete Repository", lambda: self.show_delete_repository_dialog())
                ])

            for label, action in actions:
                ui.button(label, on_click=action).style('width: 100%; text-align: left; background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;')

    def render_members_preview(self):
        with ui.column().style('background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;'):
            ui.html('<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px;">Members</h3>')

            try:
                members = self.api_service.get_repository_members(self.selected_repo["id"])[:3]
            except Exception as e:
                ui.notify(f"Failed to load members: {str(e)}", type='negative')
                members = []

            for member in members:
                with ui.row().style('display: flex; align-items: center; gap: 12px; margin-bottom: 12px;'):
                    ui.html('<div style="width: 32px; height: 32px; background-color: #dbeafe; color: #2563eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;">👤</div>')
                    ui.html(f'<div><div style="font-weight: 500;">{member["username"]}</div><div style="font-size: 12px; color: #6b7280;">{member["role"]}</div></div>')

            try:
                total_members = len(self.api_service.get_repository_members(self.selected_repo["id"]))
                if total_members > 3:
                    ui.html(f'<div style="text-align: center; font-size: 12px; color: #6b7280;">... and {total_members - 3} more</div>')
            except Exception as e:
                pass

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

        # Update sidebar selection appearance
        for repo_id, container in self.repo_containers.items():
            if repo_id == repo["id"]:
                # Selected style
                container.style('width: 100%; padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 2px solid #3b82f6; background-color: #dbeafe;')
            else:
                # Unselected style
                container.style('width: 100%; padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 1px solid #e5e7eb; background-color: white;')

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

        try:
            # GitHub URL에서 repository name 추출
            # 예: https://github.com/owner/repo -> repo
            repo_name = url.rstrip('/').split('/')[-1]

            # API 호출하여 repository 생성
            self.api_service.create_repository(
                name=repo_name,
                url=url,
                description=description or f"Repository: {repo_name}",
                is_public=False
            )

            ui.notify(f'Repository "{repo_name}" added successfully! Processing will start shortly.', color='green')
            dialog.close()

            # 페이지 새로고침하여 새 repository 표시
            ui.navigate.reload()

        except Exception as e:
            ui.notify(f'Failed to add repository: {str(e)}', color='red')

    def show_members_dialog(self):
        with ui.dialog() as dialog, ui.card().style('width: 600px;'):
            with ui.row().style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;'):
                ui.html('<h3 style="font-size: 18px; font-weight: 600;">Repository Members</h3>')
                ui.button('➕ Invite Member', on_click=lambda: self.show_invite_member_dialog(dialog)).style('background-color: #3b82f6; color: white; padding: 6px 12px; border-radius: 4px; border: none; font-size: 12px;')

            try:
                members = self.api_service.get_repository_members(self.selected_repo["id"])
            except Exception as e:
                ui.notify(f"Failed to load members: {str(e)}", type='negative')
                members = []

            with ui.column().style('gap: 8px; max-height: 400px; overflow-y: auto;'):
                for member in members:
                    with ui.row().style('display: flex; align-items: center; justify-content: space-between; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px;'):
                        with ui.row().style('display: flex; align-items: center; gap: 12px;'):
                            ui.html('<div style="width: 40px; height: 40px; background-color: #dbeafe; color: #2563eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px;">👤</div>')
                            with ui.column().style('gap: 2px;'):
                                ui.html(f'<div style="font-weight: 500; font-size: 14px;">{member["username"]}</div>')
                                ui.html(f'<div style="font-size: 12px; color: #6b7280;">{member["email"]}</div>')
                                ui.html(f'<div style="font-size: 11px; color: #9ca3af;">Joined {member["joined_at"].strftime("%b %d, %Y")}</div>')

                        with ui.row().style('display: flex; align-items: center; gap: 8px;'):
                            # Role dropdown
                            role_select = ui.select(['admin', 'member'], value=member["role"], on_change=lambda e, m=member: self.change_member_role(m, e.value)).style('min-width: 80px; font-size: 12px;')

                            # Action buttons (only show if not current user or if admin)
                            current_user = self.auth_service.get_current_user()
                            if current_user["email"] != member["email"]:
                                ui.button('🚪', on_click=lambda m=member: self.kick_member(m, dialog)).style('background-color: #fef2f2; color: #dc2626; padding: 4px; border-radius: 4px; border: none; font-size: 12px; cursor: pointer;').tooltip('Remove member')

            ui.button('Close', on_click=dialog.close).style('width: 100%; margin-top: 16px; background-color: #6b7280; color: white; padding: 8px; border-radius: 4px; border: none;')

        dialog.open()

    def trigger_sync(self):
        ui.notify('Synchronization started...', color='blue')

    def show_sync_logs(self):
        ui.notify('Sync logs feature coming soon', color='blue')

    def show_repository_settings(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Repository Settings</h3>')

            with ui.column().classes('gap-4'):
                ui.input('Repository Name', value=self.selected_repo["name"]).classes('w-full')
                ui.textarea('Description', value=self.selected_repo["description"]).classes('w-full')

                with ui.row().classes('items-center gap-2'):
                    ui.label('Auto Sync')
                    ui.switch(value=True)

                with ui.row().classes('items-center gap-2'):
                    ui.label('Public Access')
                    ui.switch(value=False)

                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary')
                    ui.button('Save Settings', on_click=lambda: self.save_repository_settings(dialog)).classes('rag-button-primary')

        dialog.open()

    def save_repository_settings(self, dialog):
        ui.notify('Repository settings saved!', color='green')
        dialog.close()

    def show_delete_repository_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold text-red-600 mb-4">Delete Repository</h3>')
            ui.html('<p class="text-gray-600 mb-4">This action cannot be undone. The repository will be permanently removed from the system.</p>')

            confirm_input = ui.input('Type "DELETE" to confirm', placeholder='DELETE').classes('w-full')

            with ui.row().classes('gap-2 mt-6 w-full'):
                ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary flex-1')
                ui.button('Delete Repository', on_click=lambda: self.delete_repository(confirm_input.value, dialog)).classes('bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex-1')

        dialog.open()

    def delete_repository(self, confirmation, dialog):
        if confirmation != "DELETE":
            ui.notify('Please type "DELETE" to confirm', color='red')
            return

        ui.notify('Repository deletion is not available in demo mode', color='blue')
        dialog.close()

    def change_member_role(self, member, new_role):
        """Change a member's role"""
        old_role = member["role"]
        if old_role != new_role:
            member["role"] = new_role
            ui.notify(f'{member["username"]} role changed from {old_role} to {new_role}', color='green')
        else:
            ui.notify('Role unchanged', color='blue')

    def kick_member(self, member, dialog):
        """Remove a member from the repository"""
        current_user = self.auth_service.get_current_user()
        if current_user["email"] == member["email"]:
            ui.notify('You cannot remove yourself', color='red')
            return

        # Show confirmation dialog
        with ui.dialog() as confirm_dialog, ui.card().style('width: 400px;'):
            ui.html(f'<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">Remove Member</h3>')
            ui.html(f'<p style="margin-bottom: 16px;">Are you sure you want to remove <strong>{member["username"]}</strong> from this repository?</p>')

            with ui.row().style('display: flex; gap: 8px; justify-content: flex-end;'):
                ui.button('Cancel', on_click=confirm_dialog.close).style('background-color: #6b7280; color: white; padding: 6px 12px; border-radius: 4px; border: none;')
                ui.button('Remove', on_click=lambda: self.confirm_kick_member(member, confirm_dialog, dialog)).style('background-color: #dc2626; color: white; padding: 6px 12px; border-radius: 4px; border: none;')

        confirm_dialog.open()

    def confirm_kick_member(self, member, confirm_dialog, members_dialog):
        """Confirm member removal"""
        # In a real app, this would remove from database
        ui.notify(f'{member["username"]} has been removed from the repository', color='green')
        confirm_dialog.close()
        members_dialog.close()
        # Refresh the members dialog
        self.show_members_dialog()

    def show_invite_member_dialog(self, parent_dialog):
        """Show dialog to invite new member"""
        with ui.dialog() as invite_dialog, ui.card().style('width: 400px;'):
            ui.html('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">Invite Member</h3>')

            with ui.column().style('gap: 12px;'):
                email_input = ui.input('Email Address', placeholder='user@example.com').style('width: 100%;')
                role_select = ui.select(['member', 'admin'], value='member', label='Role').style('width: 100%;')

                with ui.row().style('display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px;'):
                    ui.button('Cancel', on_click=invite_dialog.close).style('background-color: #6b7280; color: white; padding: 6px 12px; border-radius: 4px; border: none;')
                    ui.button('Send Invite', on_click=lambda: self.send_invite(email_input.value, role_select.value, invite_dialog)).style('background-color: #3b82f6; color: white; padding: 6px 12px; border-radius: 4px; border: none;')

        invite_dialog.open()

    def send_invite(self, email, role, dialog):
        """Send invitation to new member"""
        if not email or '@' not in email:
            ui.notify('Please enter a valid email address', color='red')
            return

        # In a real app, this would send an actual invitation
        ui.notify(f'Invitation sent to {email} as {role}', color='green')
        dialog.close()