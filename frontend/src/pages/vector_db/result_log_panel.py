# src/pages/vectorDB/result_log_panel.py

from nicegui import ui
from collections import deque


class ResultLogPanel:

    def __init__(self, max_logs: int = 50):

        self.logs = deque(maxlen=max_logs)
        self.container = None

    def add_log(self, message: str):
        if self.container:
            self.logs.appendleft(f"➡️ {message}")
            self.container.clear()
            with self.container:
                for log in self.logs:
                    ui.label(log).classes('text-sm text-gray-600')

    def render(self):
        self.container = ui.column().classes('w-full')
        return self.container