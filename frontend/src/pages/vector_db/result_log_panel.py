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

    def add_log(self, message: str):
        if self.container:
            self.logs.appendleft(message)
            self.container.clear()
            with self.container:
                for log in self.logs:
                    ui.markdown(log).style(
                        "font-size: 13px; line-height: 1.35; white-space: normal;"
                    )

    def render(self):
        self.container = ui.column().classes('w-full')
        return self.container


def format_search_results(results: list[dict]) -> str:
    if not results:
        return "⚠️ 검색 결과가 없습니다."

    parts = []
    for idx, r in enumerate(results, 1):
        rid = str(r.get('id', 'N/A'))
        dist = r.get('distance')
        dist_str = f"{dist:.4f}" if isinstance(dist, (int, float)) else "N/A"

        path = r.get('file_path', '') or ''
        typ  = r.get('type', '') or ''
        name = r.get('name', '') or ''

        # text/code 스니펫은 코드블록으로 고정폭 표시 + 줄바꿈 유지
        snippet = r.get('text') or r.get('code_preview') or ''
        snippet = snippet[:1200]  # 너무 길면 조금 잘라서
        snippet_block = _fence_code(snippet, "text")

        parts.append(
            "\n".join([
                f"**[{idx}]** ID: {_inline(rid)} · 유사도: {dist_str}",
                f"📂 Path: {_inline(path)}",
                f"🔖 Type: {_inline(typ)} · Name: {_inline(name)}",
                f"💻 Snippet:\n{snippet_block}",
                "---",
            ])
        )
    return "\n".join(parts)
