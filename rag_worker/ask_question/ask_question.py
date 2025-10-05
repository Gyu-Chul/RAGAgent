import openai
import os
from dotenv import load_dotenv

from typing import List, Optional
from .types import ChatMessage
from .exceptions import UnsupportedModelError, LLMAPIError

class AskQuestion:
    """입력받은 프롬프트를 LLM API를 통해 req/res 받는 클래스"""

    def __init__(self):
        """AskQuestion 초기화 - API 키는 실제 호출 시 체크"""
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.client = None

    # 사용 가능한 모델 리스트
    MODELS: List[str] = ["gpt-3.5-turbo", 
                         "gpt-3.5-turbo-1106", 
                         "gpt-3.5-turbo-0125", 
                         "gpt-4o-mini"]

    def ask_question(
        self,
        prompt: str,
        use_stream: Optional[bool] = False,
        model: Optional[str] = "gpt-3.5-turbo",
        temperature: Optional[float] = 0.1,
        max_tokens: Optional[int] = 1024,
    ) -> str:
        """
        하나의 요청 객체를 받아 GPT 모델에게 질문하고 답변 출력

        Args:
            prompt: 질문에 사용될 프롬프트
            use_stream: 스트리밍 사용 여부
            model: 사용될 모델
            temperature: gpt 답변 온도
            max_tokens: 질문에 사용될 최대 토큰 수

        Return:
            LLM의 res 답변

        Raises:
            UnsupportedModelError: 지원하지 않는 모델을 요청했을 시
            LLMAPIError: OpenAI API 호출 실패 시

        """

        # API 키 체크
        if not self.api_key or not self.client:
            raise LLMAPIError("OPENAI_API_KEY가 설정되지 않았습니다. 환경 변수를 확인해주세요.")

        if model not in self.MODELS:
            raise UnsupportedModelError(f"지원하지 않는 모델입니다: '{model}'. 지원 모델: {self.MODELS}")
        
        system_prompt = """
        ## CORE MISSION
        당신은 사용자가 제공한 소스 코드 'CONTEXT'를 심층적으로 분석하여 'QUESTION'에 답변하는 AI 코드 분석 전문가입니다.

        ## IMPORTANT NOTES
        - 제공된 CONTEXT는 하나의 프로젝트에서 추출된 **여러 코드 조각**입니다
        - 각 조각은 작을 수 있지만, **모든 조각을 종합적으로 분석**하여 질문에 답변하세요
        - 여러 출처의 코드를 **조합하고 연결**하여 전체 로직을 설명할 수 있습니다

        ## ANALYSIS STRATEGY
        1. **전체 맥락 파악**: 모든 코드 조각을 읽고 전체적인 흐름을 이해하세요
        2. **관련 코드 식별**: 질문과 관련된 모든 코드 조각을 찾으세요
        3. **조각 연결**: 여러 조각을 논리적으로 연결하여 설명하세요
        4. **구체적 답변**: 코드를 인용하며 명확하게 답변하세요

        ## OUTPUT STYLE
        - **파일/위치 명시**: 코드의 출처를 명확히 밝히세요
        - **코드 인용**: 설명에 관련 코드를 포함하세요
        - **단계별 설명**: 복잡한 로직은 단계별로 설명하세요
        - **Markdown 활용**: 가독성 있게 포맷팅하세요

        ## IMPORTANT
        - CONTEXT의 코드 조각이 작더라도, **여러 조각을 종합하여** 답변할 수 있습니다
        - 질문에 답변할 수 있는 충분한 정보가 있다면 반드시 답변하세요
        - 정말로 관련 정보가 전혀 없을 때만 "답변할 수 없습니다"라고 하세요
        """


        # API 호출
        messages: List[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=use_stream,
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_content = ""
            if use_stream:
                for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        response_content += delta
            else:
                response_content = resp.choices[0].message.content or ""

            return response_content

        except openai.APIError as e:
            print(f"❌ OpenAI API 호출 중 오류 발생: {e}")
            raise LLMAPIError(f"OpenAI API 호출 중 오류가 발생했습니다: {e}") from e

