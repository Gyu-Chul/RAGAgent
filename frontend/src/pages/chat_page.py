from nicegui import ui
import asyncio
from datetime import datetime
from src.components.header import Header
from src.services.api_service import APIService

class ChatPage:
    def __init__(self, repo_id: str, auth_service):
        self.repo_id = repo_id
        self.auth_service = auth_service
        self.api_service = APIService(auth_service=auth_service)
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
        self.sidebar_container = None

    def render(self):
        if not self.repository:
            return self.render_not_found()

        # Main container - full viewport height
        with ui.element('div').style('height: 100vh; display: flex; flex-direction: column; overflow: hidden;'):
            # Header
            Header(self.auth_service).render()

            # Main content area
            with ui.element('div').style('flex: 1; display: flex; overflow: hidden;'):
                # Sidebar container
                self.sidebar_container = ui.element('div')
                with self.sidebar_container:
                    self.render_sidebar()

                # Chat area container
                self.chat_area_container = ui.element('div').style('flex: 1; display: flex; flex-direction: column; overflow: hidden;')
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

        with ui.element('div').style('width: 280px; background-color: #f8fafc; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; overflow: hidden;'):
            # Header
            with ui.element('div').style('padding: 16px; border-bottom: 1px solid #e2e8f0;'):
                with ui.row().classes('items-center gap-3 mb-3'):
                    ui.html('<span style="color: #2563eb; font-size: 24px;">💬</span>')
                    ui.html('<h2 class="text-xl font-bold">Chat Rooms</h2>')

                with ui.element('div').style('width: 100%;'):
                    ui.button('➕ New Chat Room', on_click=self.show_create_chat_dialog).classes('rag-button-primary').style('width: 100%;')

            # Chat rooms list
            with ui.element('div').style('flex: 1; overflow-y: auto; padding: 12px;'):
                for room in chat_rooms:
                    self.render_chat_room_item(room)

    def render_chat_room_item(self, room):
        is_selected = self.selected_chat_room and self.selected_chat_room["id"] == room["id"]
        room_id = room["id"]

        if is_selected:
            bg_color = "#dbeafe"
            border_color = "#3b82f6"
        else:
            bg_color = "white"
            border_color = "transparent"

        # Create a container for this specific room
        with ui.element('div').style(f'display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px; border-radius: 10px; background-color: {bg_color}; border: 2px solid {border_color}; margin-bottom: 6px; transition: all 0.2s; height: 52px; width: 100%;') as container:
            # Room name container - clickable
            with ui.element('div').style('flex: 1; min-width: 0; cursor: pointer;').on('click', lambda rid=room_id: self.handle_room_click_only(rid)):
                ui.html(f'<span style="font-weight: 500; font-size: 14px; color: #1f2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;">{room["name"]}</span>')

            # Options button (fixed position on right) - separate click handler
            with ui.element('div').style('flex-shrink: 0;'):
                ui.button('⋮', on_click=lambda rid=room_id: self.handle_options_click_only(rid)).style('color: #6b7280; padding: 4px 8px; background: transparent; border: none; font-size: 18px; cursor: pointer; border-radius: 6px; min-width: 32px;').props('flat dense')

    def render_chat_area(self):
        with ui.element('div').style('flex: 1; display: flex; flex-direction: column; overflow: hidden;'):
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

        with ui.element('div').style('flex: 1; display: flex; flex-direction: column; overflow: hidden;'):
            # Chat header - fixed height
            self.render_chat_header()

            # Messages area - flexible height with scroll
            with ui.element('div').style('flex: 1; overflow: hidden; display: flex; flex-direction: column;'):
                self.render_messages_area()

            # Input area - fixed height
            self.render_input_area()

    def render_chat_header(self):
        room = self.selected_chat_room

        with ui.element('div').style('padding: 20px 24px; border-bottom: 1px solid #e5e7eb; background-color: white; display: flex; align-items: center; height: 80px;'):
            ui.html('<span style="color: #2563eb; font-size: 24px; margin-right: 12px;">💬</span>')
            with ui.column().classes('gap-1').style('flex: 1; min-width: 0;'):
                ui.html(f'<h3 style="font-weight: 600; font-size: 18px; color: #111827; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{room["name"]}</h3>')
                ui.html(f'<p style="font-size: 13px; color: #6b7280; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{self.repository["name"]} • {room["message_count"]} messages</p>')

    def render_messages_area(self):
        # Messages container - fixed size regardless of content
        with ui.element('div').style('flex: 1; overflow-y: auto; padding: 24px; background-color: #f9fafb; min-height: 0; width: 100%;').props('id=messages-container') as container:
            self.messages_container = container

            # Inner container for messages - centered with max width
            with ui.element('div').style('max-width: 1200px; margin: 0 auto; width: 100%; min-height: 100%; display: flex; flex-direction: column;'):
                try:
                    messages = self.api_service.get_messages(self.selected_chat_room["id"])
                except Exception as e:
                    ui.notify(f"Failed to load messages: {str(e)}", type='negative')
                    messages = []

                # Render messages with consistent spacing
                for i, message in enumerate(messages):
                    self.render_message(message)

    def render_message(self, message):
        is_user = message["sender"] == "user"

        with ui.element('div').style('width: 100%; margin-bottom: 20px; display: flex; align-items: flex-start;'):
            if is_user:
                # User message - right aligned with fixed width
                ui.element('div').style('flex: 1; min-width: 0;')  # spacer
                with ui.element('div').style('width: 600px; max-width: 600px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 18px; border-radius: 18px 18px 4px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'):
                    ui.html(f'<div style="white-space: pre-wrap; line-height: 1.5; word-break: break-word;">{message["content"]}</div>')
                    ui.html(f'<div style="font-size: 11px; opacity: 0.8; margin-top: 8px; text-align: right;">{message["timestamp"].strftime("%H:%M")}</div>')
            else:
                # AI message - left aligned with fixed width
                with ui.element('div').style('width: 700px; max-width: 700px; background: white; border: 1px solid #e5e7eb; border-radius: 18px 18px 18px 4px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden;'):

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

                ui.element('div').style('flex: 1;')  # spacer

    def render_input_area(self):
        with ui.element('div').style('padding: 24px; border-top: 1px solid #e5e7eb; background-color: white;'):
            with ui.element('div').style('max-width: 1200px; margin: 0 auto; display: flex; gap: 16px; align-items: flex-end;'):
                # Text input
                self.message_input = ui.textarea(
                    placeholder=f'Ask anything about {self.repository["name"]}... (Press Enter to send, Shift+Enter for new line)'
                ).style('''
                    flex: 1;
                    min-height: 60px;
                    max-height: 200px;
                    padding: 16px 20px;
                    border: 2px solid #e2e8f0;
                    border-radius: 16px;
                    font-size: 15px;
                    line-height: 1.5;
                    resize: vertical;
                    font-family: system-ui, -apple-system, sans-serif;
                    transition: border-color 0.2s;
                ''').props('autofocus')

                # Add Enter key handling (Shift+Enter for newline)
                self.message_input.on('keydown.enter', lambda e: None if e.args.get('shiftKey') else self.send_message())

                # Send button
                ui.button('Send', icon='send', on_click=self.send_message).style('''
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 18px 36px;
                    border-radius: 12px;
                    border: none;
                    cursor: pointer;
                    font-size: 15px;
                    font-weight: 600;
                    min-width: 120px;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
                    transition: all 0.2s;
                ''').props('flat')


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


    def handle_room_click(self, e, room_id):
        """Handle room selection click"""
        # Find the room by id
        try:
            chat_rooms = self.api_service.get_chat_rooms(self.repo_id)
            room = next((r for r in chat_rooms if r["id"] == room_id), None)
            if room:
                self.select_chat_room(room)
        except Exception as ex:
            print(f"Error selecting room: {ex}")

    def handle_options_click(self, e, room_id):
        """Handle options button click"""
        # Stop event propagation to prevent room selection
        e.handled = True

        # Find the room by id
        try:
            chat_rooms = self.api_service.get_chat_rooms(self.repo_id)
            room = next((r for r in chat_rooms if r["id"] == room_id), None)
            if room:
                self.show_room_options(room, e)
        except Exception as ex:
            print(f"Error showing room options: {ex}")

    def handle_room_click_only(self, room_id):
        """Handle room name click to select room (no event object)"""
        try:
            chat_rooms = self.api_service.get_chat_rooms(self.repo_id)
            room = next((r for r in chat_rooms if r["id"] == room_id), None)
            if room:
                self.select_chat_room(room)
        except Exception as ex:
            print(f"Error selecting room: {ex}")

    def handle_options_click_only(self, room_id):
        """Handle options button click to show modal (no event object)"""
        try:
            chat_rooms = self.api_service.get_chat_rooms(self.repo_id)
            room = next((r for r in chat_rooms if r["id"] == room_id), None)
            if room:
                self.show_room_options(room, None)
        except Exception as ex:
            print(f"Error showing options: {ex}")

    def select_chat_room(self, room):
        self.selected_chat_room = room

        # Update the sidebar to show correct selection
        self.sidebar_container.clear()
        with self.sidebar_container:
            self.render_sidebar()

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

    def show_room_options(self, room, event):
        # Stop event propagation to prevent room selection
        if event:
            event.stop_propagation = True

        with ui.dialog() as dialog, ui.card().style('width: 320px; padding: 24px;'):
            ui.html(f'<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #111827;">{room["name"]}</h3>')

            ui.button('🗑️ Delete Room', on_click=lambda: self.delete_room(room, dialog)).style('''
                background: #fef2f2;
                color: #dc2626;
                padding: 12px 20px;
                border-radius: 8px;
                width: 100%;
                border: 1px solid #fecaca;
                cursor: pointer;
                font-weight: 500;
                font-size: 14px;
            ''')

            ui.button('Cancel', on_click=dialog.close).style('''
                background: #f3f4f6;
                color: #374151;
                padding: 12px 20px;
                border-radius: 8px;
                width: 100%;
                border: none;
                cursor: pointer;
                font-weight: 500;
                font-size: 14px;
                margin-top: 8px;
            ''')

        dialog.open()

    def delete_room(self, room, dialog):
        ui.notify('Room deletion is not available in demo mode', color='blue')
        dialog.close()