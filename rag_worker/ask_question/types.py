"""
LLM API 관련 타입 정의
"""

from typing import TypedDict, Optional

### prompt
class SearchResultItem(TypedDict):
    """검색 결과 아이템"""

    code: str
    file_path: str
    name: str
    start_line: int
    end_line: int
    type: str
    _source_file: str
    score: Optional[float]
    
### ask_question
class LLMRequest(TypedDict):
    """ask_question 함수 input 타입"""

    prompt: str
    use_stream: Optional[bool]
    model: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]


class ChatMessage(TypedDict):
    """OpenAI API에 전달될 메시지 형식"""

    role: str
    content: str


