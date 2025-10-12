from nicegui import ui

class AuthPage:
    def __init__(self, auth_service, mode: str = 'login'):
        self.mode = mode
        self.auth_service = auth_service

    def render(self):
        with ui.row().classes('w-full h-screen items-center justify-center').style('background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)'):
            with ui.card().classes('w-96 p-8'):
                with ui.column().classes('w-full gap-6'):
                    ui.html('<div class="text-center"><h1 class="text-3xl font-bold text-gray-800 mb-2">RAGIT</h1><p class="text-gray-600">Transform GitHub repos into intelligent RAG systems</p></div>')

                    if self.mode == 'login':
                        self.render_login_form()
                    else:
                        self.render_signup_form()

    def render_login_form(self):
        with ui.column().classes('w-full gap-4'):
            ui.label('Sign In').classes('text-xl font-semibold text-center')

            email_input = ui.input('Email', placeholder='Enter your email').classes('rag-input w-full')
            password_input = ui.input('Password', placeholder='Enter your password', password=True).classes('rag-input w-full')

            login_btn = ui.button('Sign In', on_click=lambda: self.handle_login(email_input.value, password_input.value)).classes('rag-button-primary w-full')

            with ui.row().classes('w-full justify-center gap-2'):
                ui.label("Don't have an account?").classes('text-sm text-gray-600')
                ui.link('Sign Up', '/signup').classes('text-sm text-blue-600 hover:text-blue-800')

            ui.separator()
            with ui.card().classes('bg-blue-50 border border-blue-200 p-4'):
                ui.label('Demo Accounts:').classes('font-semibold text-blue-800 mb-2')
                ui.label('Admin: admin@ragit.com / admin123').classes('text-sm text-blue-700')
                ui.label('User: user@ragit.com / user123').classes('text-sm text-blue-700')

    def render_signup_form(self):
        with ui.column().classes('w-full gap-4'):
            ui.label('Create Account').classes('text-xl font-semibold text-center')

            name_input = ui.input('Full Name', placeholder='Enter your full name').classes('rag-input w-full')
            username_input = ui.input('Username', placeholder='Enter username').classes('rag-input w-full')
            email_input = ui.input('Email', placeholder='Enter your email').classes('rag-input w-full')
            password_input = ui.input('Password', placeholder='Create a password', password=True).classes('rag-input w-full')

            signup_btn = ui.button('Create Account', on_click=lambda: self.handle_signup(
                username_input.value,
                email_input.value,
                password_input.value,
                name_input.value
            )).classes('rag-button-primary w-full')

            with ui.row().classes('w-full justify-center gap-2'):
                ui.label("Already have an account?").classes('text-sm text-gray-600')
                ui.link('Sign In', '/login').classes('text-sm text-blue-600 hover:text-blue-800')

    def handle_login(self, email: str, password: str):
        if not email or not password:
            ui.notify('Please fill in all fields', color='red')
            return

        result = self.auth_service.login(email, password)
        if result['success']:
            ui.notify('Login successful!', color='green')
            ui.navigate.to('/main')
        else:
            ui.notify(result['message'], color='red')

    def handle_signup(self, username: str, email: str, password: str, name: str):
        if not all([username, email, name]):
            ui.notify('Please fill in all fields', color='red')
            return

        result = self.auth_service.signup(username, email, password, name)
        if result['success']:
            ui.notify('Account created successfully! Please login.', color='green')
            ui.navigate.to('/login')
        else:
            ui.notify(result['message'], color='red')