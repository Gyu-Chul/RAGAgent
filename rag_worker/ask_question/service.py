"""
LLM 질문 요청 서비스
"""

from typing import List, Dict, Any, Optional

from .ask_question import AskQuestion
from .prompt_generator import PromptGenerator
from .types import SearchResultItem, LLMRequest, ChatMessage
from .exceptions import LLMError, NoContextFoundError, PromptCreationError, ValueError, UnsupportedModelError, LLMAPIError

class AskCaller:
    """LLM에게 질문하는 클래스"""

    def __init__(self) -> None:
        """AskQuestion, PromptGenerator 초기화"""
        self.ask: AskQuestion = AskQuestion()
        self.prompt: PromptGenerator = PromptGenerator()

    def create(self, docs: List[SearchResultItem], query: str) -> str:
        """
        단일 Python 파일을 청킹

        Args:
            file_path: 파싱할 Python 파일 경로

        Returns:
            파싱 결과
        """
        return self.PromptGenerator.create(docs=docs, query=query)
    

    def ask_question(
        self, 
        prompt: str, 
        use_stream: Optional[bool] = False, 
        model: Optional[str] = "gpt-3.5-turbo", 
        temperature: Optional[float] = 0.1, 
        max_tokens: Optional[int] = 1024,
    ) -> str:
        """
        단일 Python 파일을 청킹

        Args:
            file_path: 파싱할 Python 파일 경로

        Returns:
            파싱 결과
        """
        return self.AskQuestion.ask_question(prompt=prompt, use_stream=use_stream, model=model, temperature=temperature, max_tokens=max_tokens) 