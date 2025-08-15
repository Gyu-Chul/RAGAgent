# src/pages/vectorDB/result_log_panel.py

from nicegui import ui
from collections import deque

# --- 유틸: 마크다운 예약문자 무해화 + 코드블록 래핑 ---
def _fence_code(text: str, lang: str = "text") -> str:
    if text is None:
        text = ""
    # 코드블록 내부에 ``` 가 있으면 깨지지 않게 분리
    safe = text.replace("```", "`\u200b``")  # backtick + zero width space
    return f"```{lang}\n{safe}\n```"

def _inline(code: str) -> str:
    if code is None:
        code = ""
    return "`" + code.replace("`", "`\u200b") + "`"

class ResultLogPanel:
    def __init__(self, max_logs: int = 50):
        self.logs = deque(maxlen=max_logs)
        self.container = None

    def add_log(self, message: str, as_code: bool = False):
        if self.container:
            self.logs.appendleft(message)
            self.container.clear()
            with self.container:
                for log in self.logs:
                    if as_code:
                        ui.markdown(f"```text\n{log}\n```").style(
                            "font-size: 13px; line-height: 1.35; white-space: pre;"
                        )
                    else:
                        ui.markdown(log).style(
                            "font-size: 13px; line-height: 1.35; white-space: normal;"
                        )
    def render(self):
        # 부모 카드의 height:100%를 온전히 상속받아 꽉 채우고 내부 스크롤
        self.container = ui.column().style(
            'width:100%; height:100%; max-height:100%; overflow-y:auto;'
        )
        return self.container

