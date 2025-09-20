from nicegui import ui
from src.components.header import Header

class AccountSettingsPage:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def render(self):
        with ui.column().classes('w-full min-h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1 p-6 gap-6 justify-center'):
                with ui.column().classes('max-w-2xl flex-1 gap-6'):
                    self.render_breadcrumb()
                    self.render_profile_section()
                    self.render_password_section()
                    self.render_account_info()

    def render_breadcrumb(self):
        with ui.row().classes('items-center gap-2 text-sm text-gray-600 mb-4'):
            ui.link('Dashboard', '/main').classes('hover:text-blue-600')
            ui.label('/').classes('text-gray-400')
            ui.label('Account Settings').classes('font-medium text-gray-800')

    def render_profile_section(self):
        user = self.auth_service.get_current_user()

        with ui.card().classes('rag-card'):
            ui.html('<h2 class="text-xl font-semibold mb-6">Profile Information</h2>')

            with ui.column().classes('gap-6'):
                with ui.row().classes('items-center gap-6'):
                    ui.html('<div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-2xl">👤</div>')
                    with ui.column().classes('flex-1'):
                        ui.html(f'<h3 class="text-lg font-medium">{user["name"]}</h3>')
                        ui.html(f'<p class="text-gray-600">{user["email"]}</p>')
                        ui.html(f'<span class="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">{user["role"].title()}</span>')

                ui.separator()

                with ui.column().classes('gap-4'):
                    ui.html('<h4 class="font-medium">Update Profile</h4>')

                    name_input = ui.input('Full Name', value=user["name"]).classes('rag-input w-full')
                    email_input = ui.input('Email', value=user["email"]).classes('rag-input w-full bg-gray-50').props('readonly')
                    ui.label('Email cannot be changed').classes('text-xs text-gray-500')

                    ui.button('💾 Update Profile', on_click=lambda: self.update_profile(name_input.value)).classes('rag-button-primary')

    def render_password_section(self):
        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Change Password</h3>')

            with ui.column().classes('gap-4'):
                current_password = ui.input('Current Password', password=True, placeholder='Enter current password').classes('rag-input w-full')
                new_password = ui.input('New Password', password=True, placeholder='Enter new password').classes('rag-input w-full')
                confirm_password = ui.input('Confirm New Password', password=True, placeholder='Confirm new password').classes('rag-input w-full')

                ui.button('🔒 Change Password', on_click=lambda: self.change_password(
                    current_password.value,
                    new_password.value,
                    confirm_password.value
                )).classes('rag-button-primary')

    def render_account_info(self):
        user = self.auth_service.get_current_user()

        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Account Information</h3>')

            info_items = [
                ("User ID", user["id"]),
                ("Username", user["username"]),
                ("Account Type", user["role"].title()),
                ("Member Since", user.get("created_at", "N/A").strftime("%B %d, %Y") if hasattr(user.get("created_at", ""), "strftime") else "N/A"),
            ]

            with ui.column().classes('gap-3'):
                for label, value in info_items:
                    with ui.row().classes('items-center justify-between py-3 border-b last:border-b-0'):
                        ui.label(label).classes('font-medium text-gray-700')
                        ui.label(str(value)).classes('text-gray-600')

            ui.separator().classes('my-4')

            with ui.column().classes('gap-3'):
                ui.html('<h4 class="font-medium text-red-600">Danger Zone</h4>')
                ui.html('<p class="text-sm text-gray-600 mb-3">These actions are irreversible. Please be careful.</p>')

                with ui.row().classes('gap-2'):
                    ui.button('📥 Download Data', on_click=self.download_data).classes('rag-button-secondary')
                    ui.button('🗑️ Delete Account', on_click=self.show_delete_confirmation).classes('bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700')

    def update_profile(self, name):
        if not name:
            ui.notify('Name cannot be empty', color='red')
            return

        result = self.auth_service.update_profile(name)
        if result['success']:
            ui.notify('Profile updated successfully!', color='green')
        else:
            ui.notify(result['message'], color='red')

    def change_password(self, current, new, confirm):
        if not all([current, new, confirm]):
            ui.notify('Please fill in all password fields', color='red')
            return

        if new != confirm:
            ui.notify('New passwords do not match', color='red')
            return

        if len(new) < 6:
            ui.notify('Password must be at least 6 characters long', color='red')
            return

        result = self.auth_service.update_profile(self.auth_service.get_current_user()["name"], new)
        if result['success']:
            ui.notify('Password changed successfully!', color='green')
        else:
            ui.notify(result['message'], color='red')

    def download_data(self):
        ui.notify('Data export will be available via email within 24 hours', color='blue')

    def show_delete_confirmation(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold text-red-600 mb-4">Delete Account</h3>')
            ui.html('<p class="text-gray-600 mb-4">This action cannot be undone. All your data, chat history, and access will be permanently deleted.</p>')

            confirm_input = ui.input('Type "DELETE" to confirm', placeholder='DELETE').classes('rag-input w-full')

            with ui.row().classes('gap-2 mt-6 w-full'):
                ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary flex-1')
                ui.button('Delete Account', on_click=lambda: self.delete_account(confirm_input.value, dialog)).classes('bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex-1')

        dialog.open()

    def delete_account(self, confirmation, dialog):
        if confirmation != "DELETE":
            ui.notify('Please type "DELETE" to confirm', color='red')
            return

        ui.notify('Account deletion is not available in demo mode', color='blue')
        dialog.close()