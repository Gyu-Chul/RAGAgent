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
        user 질문 프롬프트 생성

        Args:
            List[SearchResultItem]: 벡터 검색 결과로 나온 데이터
            query: 사용자 질문 str

        Returns:
            user_prompt
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
        system prompt 연결 및 call API

        Args:
            prompt: user prompt
            use_stream: 스트리밍 사용 여부
            model: 원하는 gpt 모델
            temperature: LLM 답변 창의성 조절
            max_token: LLM 사용 토큰 제한

        Returns:
            LLM의 최종 답변
        """
        return self.AskQuestion.ask_question(prompt=prompt, use_stream=use_stream, model=model, temperature=temperature, max_tokens=max_tokens) 