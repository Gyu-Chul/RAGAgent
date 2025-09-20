from nicegui import ui
import asyncio
from datetime import datetime
from src.components.header import Header
from src.data.dummy_data import DummyDataService

class ChatPage:
    def __init__(self, repo_id: str, auth_service):
        self.repo_id = repo_id
        self.auth_service = auth_service
        self.data_service = DummyDataService()
        self.repository = self.data_service.get_repository(repo_id)
        self.selected_chat_room = None
        self.message_input = None
        self.messages_container = None

    def render(self):
        if not self.repository:
            return self.render_not_found()

        with ui.column().classes('w-full h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1 overflow-hidden'):
                self.render_sidebar()
                self.render_chat_area()

    def render_not_found(self):
        with ui.column().classes('w-full min-h-screen items-center justify-center'):
            ui.html('<h2 class="text-2xl font-bold text-gray-600">Repository Not Found</h2>')
            ui.button('Back to Repositories', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-primary mt-4')

    def render_sidebar(self):
        chat_rooms = self.data_service.get_chat_rooms(self.repo_id)

        with ui.column().classes('rag-sidebar w-80 h-full overflow-y-auto'):
            with ui.column().classes('p-6 gap-4 h-full'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.icon('chat').classes('text-blue-600 text-xl')
                    ui.html('<h2 class="text-lg font-semibold">Chat Rooms</h2>')

                ui.button('New Chat Room', icon='add', on_click=self.show_create_chat_dialog).classes('rag-button-primary w-full')

                with ui.column().classes('gap-2 flex-1 overflow-y-auto'):
                    for room in chat_rooms:
                        self.render_chat_room_item(room)

                ui.separator().classes('my-4')

                with ui.column().classes('gap-2'):
                    if self.auth_service.is_admin():
                        ui.button('Repository Settings', icon='settings', on_click=lambda: ui.navigate.to(f'/admin/repository/{self.repo_id}')).classes('rag-button-secondary w-full text-sm')

                    ui.button('Back to Dashboard', icon='dashboard', on_click=lambda: ui.navigate.to('/main')).classes('rag-button-secondary w-full text-sm')

    def render_chat_room_item(self, room):
        is_selected = self.selected_chat_room and self.selected_chat_room["id"] == room["id"]
        button_classes = "w-full text-left p-3 rounded-lg transition-colors"
        if is_selected:
            button_classes += " bg-blue-100 border-blue-300"
        else:
            button_classes += " hover:bg-gray-100"

        with ui.button(on_click=lambda r=room: self.select_chat_room(r)).classes(button_classes):
            with ui.column().classes('gap-1 w-full'):
                with ui.row().classes('items-center gap-2 w-full justify-between'):
                    ui.html(f'<span class="font-medium truncate">{room["name"]}</span>')
                    ui.button(icon='more_vert', on_click=lambda r=room: self.show_room_options(r)).classes('text-gray-400 p-1')

                ui.html(f'<div class="text-sm text-gray-600 truncate">{room["last_message"]}</div>')

                with ui.row().classes('items-center gap-3 text-xs text-gray-500 mt-1'):
                    ui.html(f'<span>💬 {room["message_count"]} messages</span>')
                    ui.html(f'<span>{room["created_at"].strftime("%b %d")}</span>')

    def render_chat_area(self):
        with ui.column().classes('flex-1 h-full'):
            if not self.selected_chat_room:
                self.render_empty_chat_state()
            else:
                self.render_active_chat()

    def render_empty_chat_state(self):
        with ui.column().classes('flex-1 items-center justify-center p-8'):
            with ui.card().classes('rag-card text-center max-w-md'):
                ui.icon('chat').classes('text-6xl text-blue-400 mb-4')
                ui.html('<h3 class="text-xl font-semibold text-gray-800 mb-2">Welcome to RAG Chat</h3>')
                ui.html(f'<p class="text-gray-600 mb-4">Start a conversation about the <strong>{self.repository["name"]}</strong> repository. Ask questions about the code, documentation, or issues.</p>')

                with ui.column().classes('gap-2 mt-4'):
                    sample_questions = [
                        "How does the authentication system work?",
                        "What are the main components of this project?",
                        "Can you explain the deployment process?",
                        "What dependencies does this project use?"
                    ]

                    ui.html('<h4 class="font-medium text-gray-700 mb-2">Try asking:</h4>')
                    for question in sample_questions:
                        with ui.card().classes('border border-gray-200 p-2 hover:bg-blue-50 cursor-pointer transition-colors text-left').on('click', lambda q=question: self.start_chat_with_question(q)):
                            ui.html(f'<span class="text-sm text-gray-700">"{question}"</span>')

    def render_active_chat(self):
        room = self.selected_chat_room

        with ui.column().classes('flex-1 h-full'):
            self.render_chat_header()

            with ui.column().classes('flex-1 overflow-hidden'):
                self.render_messages_area()

            self.render_input_area()

    def render_chat_header(self):
        room = self.selected_chat_room

        with ui.row().classes('items-center justify-between p-4 border-b bg-white'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('chat').classes('text-blue-600')
                with ui.column():
                    ui.html(f'<h3 class="font-semibold">{room["name"]}</h3>')
                    ui.html(f'<p class="text-sm text-gray-600">{self.repository["name"]} • {room["message_count"]} messages</p>')

            with ui.row().classes('items-center gap-2'):
                ui.button('Clear Chat', icon='clear_all', on_click=self.clear_chat).classes('rag-button-secondary text-sm')
                if self.auth_service.is_admin():
                    ui.button('Repository Settings', icon='settings', on_click=lambda: ui.navigate.to(f'/admin/repository/{self.repo_id}')).classes('rag-button-secondary text-sm')

    def render_messages_area(self):
        with ui.column().classes('flex-1 overflow-y-auto p-4 gap-4').props('id=messages-container') as container:
            self.messages_container = container
            messages = self.data_service.get_messages(self.selected_chat_room["id"])

            for message in messages:
                self.render_message(message)

    def render_message(self, message):
        is_user = message["sender"] == "user"

        with ui.row().classes('w-full'):
            if is_user:
                ui.element().classes('flex-1')  # spacer
                with ui.card().classes('rag-chat-bubble rag-chat-user max-w-2xl'):
                    ui.html(f'<div class="whitespace-pre-wrap">{message["content"]}</div>')
                    ui.html(f'<div class="text-xs opacity-75 mt-2">{message["timestamp"].strftime("%H:%M")}</div>')
            else:
                with ui.card().classes('rag-chat-bubble rag-chat-bot max-w-4xl'):
                    ui.html(f'<div class="whitespace-pre-wrap">{message["content"]}</div>')

                    if message.get("sources"):
                        ui.separator().classes('my-3')
                        ui.html('<div class="text-sm font-medium text-gray-700 mb-2">📚 Sources:</div>')
                        with ui.column().classes('gap-1'):
                            for source in message["sources"]:
                                with ui.row().classes('items-center gap-2 text-sm text-blue-600 hover:text-blue-800 cursor-pointer'):
                                    ui.icon('description').classes('text-sm')
                                    ui.html(f'<span>{source}</span>')

                    ui.html(f'<div class="text-xs text-gray-500 mt-2">{message["timestamp"].strftime("%H:%M")}</div>')

                ui.element().classes('flex-1')  # spacer

    def render_input_area(self):
        with ui.row().classes('p-4 border-t bg-white gap-2'):
            self.message_input = ui.input(
                placeholder=f'Ask anything about {self.repository["name"]}...',
                on_keydown=self.handle_keydown
            ).classes('rag-input flex-1')

            with ui.button(icon='send', on_click=self.send_message).classes('rag-button-primary'):
                pass

            ui.button(icon='attach_file', on_click=self.show_attachment_options).classes('rag-button-secondary')

    def handle_keydown(self, e):
        if e.key == 'Enter' and not e.shift:
            self.send_message()

    async def send_message(self):
        if not self.message_input.value.strip():
            return

        message_content = self.message_input.value.strip()
        self.message_input.value = ""

        user_message = self.data_service.add_message(
            self.selected_chat_room["id"],
            "user",
            message_content
        )

        with self.messages_container:
            self.render_message(user_message)

        await self.simulate_bot_response(message_content)

    async def simulate_bot_response(self, user_message: str):
        await asyncio.sleep(1)

        bot_responses = {
            "authentication": "The authentication system in this repository uses JWT tokens with a custom middleware. You can find the implementation in `auth/middleware.py`. The main components include:\n\n1. **Token Generation**: Uses the `generate_jwt_token()` function\n2. **Token Validation**: Handled by `validate_token_middleware()`\n3. **User Session Management**: Managed through the `UserSession` class\n\nThe system supports both cookie-based and header-based authentication.",
            "components": "This project has several main components:\n\n**Backend Services:**\n- API Gateway (`/gateway`)\n- Authentication Service (`/auth`)\n- Vector Database Service (`/vectordb`)\n- RAG Processing Engine (`/rag`)\n\n**Frontend:**\n- React Dashboard (`/frontend`)\n- Admin Panel (`/admin`)\n\n**Infrastructure:**\n- Docker containers for each service\n- Kubernetes deployment configs\n- CI/CD pipeline with GitHub Actions",
            "deployment": "The deployment process follows a GitOps approach:\n\n1. **Local Development**: Use `docker-compose up` to run all services\n2. **Staging**: Automatic deployment to staging on PR merge\n3. **Production**: Manual approval required, deployed via Kubernetes\n\n**Key files:**\n- `docker-compose.yml` - Local development\n- `k8s/` - Kubernetes manifests\n- `.github/workflows/` - CI/CD pipelines\n\nThe system uses rolling deployments with health checks.",
            "dependencies": "This project uses modern dependencies:\n\n**Backend (Python):**\n- FastAPI for API framework\n- Celery for async task processing\n- Redis for caching and message queuing\n- PostgreSQL for primary database\n- Milvus for vector storage\n\n**Frontend (React):**\n- Next.js for the React framework\n- Tailwind CSS for styling\n- React Query for state management\n- TypeScript for type safety\n\nAll dependencies are managed through `requirements.txt` and `package.json`."
        }

        response_content = "I can help you understand this repository! Based on your question, let me provide you with relevant information from the codebase."

        for keyword, response in bot_responses.items():
            if keyword in user_message.lower():
                response_content = response
                break

        bot_message = self.data_service.add_message(
            self.selected_chat_room["id"],
            "bot",
            response_content
        )

        if "authentication" in user_message.lower():
            bot_message["sources"] = ["auth/middleware.py", "auth/models.py", "docs/authentication.md"]
        elif "components" in user_message.lower():
            bot_message["sources"] = ["README.md", "docker-compose.yml", "architecture.md"]
        elif "deployment" in user_message.lower():
            bot_message["sources"] = ["k8s/deployment.yaml", ".github/workflows/deploy.yml", "docs/deployment.md"]
        elif "dependencies" in user_message.lower():
            bot_message["sources"] = ["requirements.txt", "package.json", "Dockerfile"]

        with self.messages_container:
            self.render_message(bot_message)

        ui.run_javascript('''
            const container = document.getElementById('messages-container');
            container.scrollTop = container.scrollHeight;
        ''')

    def select_chat_room(self, room):
        self.selected_chat_room = room
        ui.update()

    def start_chat_with_question(self, question):
        if not self.selected_chat_room:
            new_room = self.data_service.create_chat_room("General Discussion", self.repo_id)
            self.selected_chat_room = new_room

        self.message_input.value = question
        ui.update()

    def show_create_chat_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Create New Chat Room</h3>')

            with ui.column().classes('gap-4'):
                name_input = ui.input('Room Name', placeholder='e.g., Feature Discussion').classes('rag-input w-full')

                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary')
                    ui.button('Create Room', on_click=lambda: self.create_chat_room(name_input.value, dialog)).classes('rag-button-primary')

        dialog.open()

    def create_chat_room(self, name, dialog):
        if not name.strip():
            ui.notify('Please enter a room name', color='red')
            return

        new_room = self.data_service.create_chat_room(name.strip(), self.repo_id)
        ui.notify(f'Chat room "{name}" created successfully!', color='green')
        dialog.close()
        ui.update()

    def show_room_options(self, room):
        with ui.dialog() as dialog, ui.card().classes('w-64'):
            ui.html(f'<h3 class="text-lg font-semibold mb-4">{room["name"]}</h3>')

            with ui.column().classes('gap-2'):
                ui.button('Rename Room', icon='edit', on_click=lambda: self.rename_room(room, dialog)).classes('rag-button-secondary w-full text-left justify-start')
                ui.button('Export Chat', icon='download', on_click=lambda: self.export_chat(room, dialog)).classes('rag-button-secondary w-full text-left justify-start')
                ui.separator()
                ui.button('Delete Room', icon='delete', on_click=lambda: self.delete_room(room, dialog)).classes('bg-red-100 text-red-700 hover:bg-red-200 w-full text-left justify-start px-4 py-2 rounded-lg')

        dialog.open()

    def rename_room(self, room, dialog):
        ui.notify('Room rename feature coming soon', color='blue')
        dialog.close()

    def export_chat(self, room, dialog):
        ui.notify('Chat export feature coming soon', color='blue')
        dialog.close()

    def delete_room(self, room, dialog):
        ui.notify('Room deletion is not available in demo mode', color='blue')
        dialog.close()

    def clear_chat(self):
        ui.notify('Chat cleared', color='green')

    def show_attachment_options(self):
        ui.notify('File attachment feature coming soon', color='blue')