from nicegui import ui
import asyncio
from datetime import datetime
from src.components.header import Header
from src.services.api_service import api_service

class ChatPage:
    def __init__(self, repo_id: str, auth_service):
        self.repo_id = repo_id
        self.auth_service = auth_service
        self.api_service = api_service
        try:
            self.repository = self.api_service.get_repository(repo_id)
            # Auto-select first chat room
            chat_rooms = self.api_service.get_chat_rooms(repo_id)
            self.selected_chat_room = chat_rooms[0] if chat_rooms else None
        except Exception as e:
            self.repository = None
            self.selected_chat_room = None
            ui.notify(f"Failed to load repository data: {str(e)}", type='negative')
        self.message_input = None
        self.messages_container = None
        self.chat_area_container = None

    def render(self):
        if not self.repository:
            return self.render_not_found()

        with ui.column().classes('w-full h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1 overflow-hidden'):
                self.render_sidebar()
                # Chat area container that can be updated
                self.chat_area_container = ui.column().classes('flex-1 h-full')
                with self.chat_area_container:
                    self.render_chat_area()

    def render_not_found(self):
        with ui.column().classes('w-full min-h-screen items-center justify-center'):
            ui.html('<h2 class="text-2xl font-bold text-gray-600">Repository Not Found</h2>')
            ui.button('Back to Repositories', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-primary mt-4')

    def render_sidebar(self):
        try:
            chat_rooms = self.api_service.get_chat_rooms(self.repo_id)
        except Exception as e:
            ui.notify(f"Failed to load chat rooms: {str(e)}", type='negative')
            chat_rooms = []

        with ui.column().classes('rag-sidebar w-80 h-full overflow-y-auto'):
            with ui.column().classes('p-6 gap-4 h-full'):
                with ui.row().classes('items-center gap-3 mb-4'):
                    ui.html('<span style="color: #2563eb; font-size: 20px;">💬</span>')
                    ui.html('<h2 class="text-lg font-semibold">Chat Rooms</h2>')

                ui.button('➕ New Chat Room', on_click=self.show_create_chat_dialog).classes('rag-button-primary w-full')

                with ui.column().classes('gap-2 flex-1 overflow-y-auto'):
                    for room in chat_rooms:
                        self.render_chat_room_item(room)

                ui.separator().classes('my-4')

                with ui.column().classes('gap-2'):
                    if self.auth_service.is_admin():
                        ui.button('⚙️ Repository Settings', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-secondary w-full text-sm')

                    ui.button('🏠 Back to Dashboard', on_click=lambda: ui.navigate.to('/main')).classes('rag-button-secondary w-full text-sm')

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
                    ui.button('⋮', on_click=lambda r=room: self.show_room_options(r)).style('color: #9ca3af; padding: 4px; background: transparent; border: none; font-size: 16px;')

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
                ui.html('<div style="font-size: 96px; color: #60a5fa; margin-bottom: 16px;">💬</div>')
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
                ui.html('<span style="color: #2563eb; font-size: 20px;">💬</span>')
                with ui.column():
                    ui.html(f'<h3 class="font-semibold">{room["name"]}</h3>')
                    ui.html(f'<p class="text-sm text-gray-600">{self.repository["name"]} • {room["message_count"]} messages</p>')

            with ui.row().classes('items-center gap-2'):
                ui.button('🗑️ Clear Chat', on_click=self.clear_chat).classes('rag-button-secondary text-sm')
                if self.auth_service.is_admin():
                    ui.button('⚙️ Repository Settings', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-secondary text-sm')

    def render_messages_area(self):
        with ui.column().classes('flex-1 overflow-y-auto p-4 gap-4').props('id=messages-container') as container:
            self.messages_container = container
            try:
                messages = self.api_service.get_messages(self.selected_chat_room["id"])
            except Exception as e:
                ui.notify(f"Failed to load messages: {str(e)}", type='negative')
                messages = []

            for message in messages:
                self.render_message(message)

    def render_message(self, message):
        is_user = message["sender"] == "user"

        with ui.row().style('width: 100%; margin-bottom: 16px;'):
            if is_user:
                # User message - right aligned
                ui.element().style('flex: 1;')  # spacer
                with ui.column().style('max-width: 70%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 18px 18px 4px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'):
                    ui.html(f'<div style="white-space: pre-wrap; line-height: 1.5;">{message["content"]}</div>')
                    ui.html(f'<div style="font-size: 11px; opacity: 0.8; margin-top: 8px; text-align: right;">{message["timestamp"].strftime("%H:%M")}</div>')
            else:
                # AI message - left aligned with RAG styling
                with ui.column().style('max-width: 85%; background: white; border: 1px solid #e5e7eb; border-radius: 18px 18px 18px 4px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden;'):

                    # AI Header with gradient
                    with ui.row().style('background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%); padding: 12px 16px; border-bottom: 1px solid #e5e7eb; align-items: center; gap: 8px;'):
                        ui.html('<div style="width: 28px; height: 28px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; font-weight: 600;">🤖</div>')
                        ui.html('<div style="font-weight: 600; color: #374151;">RAGIT</div>')
                        ui.html('<div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 500;">AI + RAG</div>')
                        ui.element().style('flex: 1;')
                        ui.html(f'<div style="font-size: 11px; color: #6b7280;">{message["timestamp"].strftime("%H:%M")}</div>')

                    # Message content
                    with ui.column().style('padding: 16px;'):
                        ui.html(f'<div style="white-space: pre-wrap; line-height: 1.6; color: #374151;">{message["content"]}</div>')

                        # Sources section with enhanced RAG styling
                        if message.get("sources"):
                            with ui.column().style('margin-top: 16px; padding: 12px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 8px; border-left: 4px solid #0ea5e9;'):
                                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px;'):
                                    ui.html('<div style="width: 20px; height: 20px; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px;">📚</div>')
                                    ui.html('<div style="font-weight: 600; color: #0f172a; font-size: 13px;">Retrieved from Repository</div>')

                                with ui.column().style('gap: 6px;'):
                                    for i, source in enumerate(message["sources"]):
                                        with ui.row().style('align-items: center; gap: 8px; padding: 6px 8px; background: rgba(255,255,255,0.7); border-radius: 6px; border: 1px solid rgba(14,165,233,0.2);'):
                                            ui.html(f'<div style="width: 16px; height: 16px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-size: 8px; font-weight: 600;">{i+1}</div>')
                                            ui.html(f'<div style="font-size: 12px; color: #1e40af; font-family: monospace;">{source}</div>')

                ui.element().style('flex: 1;')  # spacer

    def render_input_area(self):
        with ui.row().style('padding: 16px; border-top: 1px solid #e5e7eb; background-color: white; gap: 8px; align-items: flex-end;'):
            self.message_input = ui.input(
                placeholder=f'Ask anything about {self.repository["name"]}...'
            ).style('flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px;')

            # Add Enter key handling
            self.message_input.on('keydown.enter', self.send_message)

            ui.button('📤 Send', on_click=self.send_message).style('background-color: #3b82f6; color: white; padding: 12px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px;')

            ui.button('📎', on_click=self.show_attachment_options).style('background-color: #6b7280; color: white; padding: 12px; border-radius: 8px; border: none; cursor: pointer;')


    def send_message(self):
        if not self.message_input.value.strip():
            return

        message_content = self.message_input.value.strip()
        self.message_input.value = ""

        try:
            result = self.api_service.add_message(
                self.selected_chat_room["id"],
                "user",
                message_content
            )

            with self.messages_container:
                self.render_message(result["user_message"])
                self.render_message(result["bot_response"])

            # Update UI and scroll to bottom
            ui.update()
            ui.run_javascript('''
                const container = document.getElementById('messages-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            ''')
        except Exception as e:
            ui.notify(f"Failed to send message: {str(e)}", type='negative')


    def select_chat_room(self, room):
        self.selected_chat_room = room
        # Update the chat area
        self.chat_area_container.clear()
        with self.chat_area_container:
            self.render_chat_area()
        ui.update()

    def start_chat_with_question(self, question):
        if not self.selected_chat_room:
            try:
                new_room = self.api_service.create_chat_room("General Discussion", self.repo_id)
            except Exception as e:
                ui.notify(f"Failed to create chat room: {str(e)}", type='negative')
                return
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

        try:
            new_room = self.api_service.create_chat_room(name.strip(), self.repo_id)
        except Exception as e:
            ui.notify(f"Failed to create chat room: {str(e)}", type='negative')
            return
        ui.notify(f'Chat room "{name}" created successfully!', color='green')
        dialog.close()
        ui.update()

    def show_room_options(self, room):
        with ui.dialog() as dialog, ui.card().classes('w-64'):
            ui.html(f'<h3 class="text-lg font-semibold mb-4">{room["name"]}</h3>')

            with ui.column().classes('gap-2'):
                ui.button('✏️ Rename Room', on_click=lambda: self.rename_room(room, dialog)).classes('rag-button-secondary w-full')
                ui.button('💾 Export Chat', on_click=lambda: self.export_chat(room, dialog)).classes('rag-button-secondary w-full')
                ui.separator()
                ui.button('🗑️ Delete Room', on_click=lambda: self.delete_room(room, dialog)).style('background: #fef2f2; color: #dc2626; padding: 8px 16px; border-radius: 6px; width: 100%; border: none; cursor: pointer;')

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