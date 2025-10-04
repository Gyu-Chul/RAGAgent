"""
LLM API 관련 타입 정의
"""

from typing import TypedDict, Optional

### prompt
class SearchResult(TypedDict):
    """벡터 DB 검색 결과로 받는 단일 문서의 형식"""
    
    file_path: str
    class_name: str
    function_name: str
    code: str

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


