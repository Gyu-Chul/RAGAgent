import openai
import os
from dotenv import load_dotenv

from typing import List, Optional
from .types import ChatMessage
from .exceptions import UnsupportedModelError, LLMAPIError

class AskQuestion:
    """입력받은 프롬프트를 LLM API를 통해 req/res 받는 클래스"""

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인하세요.")

    client = openai.OpenAI(api_key=api_key)

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
        
        if model not in self.MODELS:
            raise UnsupportedModelError(f"지원하지 않는 모델입니다: '{model}'. 지원 모델: {self.MODELS}")
        
        system_prompt = """
        ## CORE MISSION
        당신은 사용자가 제공한 소스 코드 'CONTEXT'를 심층적으로 분석하여 'QUESTION'에 답변하는 AI 코드 분석 전문가입니다. 당신의 답변은 반드시 개발자가 이해하기 쉽고 명확해야 합니다.

        ## GOLDEN RULES (매우 중요)
        1.  **CONTEXT-ONLY**: 답변은 **오직** 제공된 'CONTEXT'에만 근거해야 합니다. 당신의 사전 지식이나 외부 정보를 절대로 사용해서는 안 됩니다.
        2.  **NO HALLUCINATION**: 'CONTEXT'에서 답변의 근거를 찾을 수 없다면, **절대로** 추측해서 답변하지 마세요. 이 경우, 반드시 "주어진 컨텍스트만으로는 질문에 답변할 수 없습니다."라고만 답변해야 합니다.

        ## OUTPUT STYLE
        - **Cite Sources**: 답변의 근거가 된 컨텍스트의 출처(파일 경로, 클래스/함수명)를 명확하게 밝혀주세요. (예: "'출처 1'의 `PromptGenerator` 클래스에 따르면...")
        - **Include Code Snippets**: 설명을 뒷받침하기 위해 'CONTEXT'에 있는 관련 코드 조각을 답변에 포함하여 이해를 도와주세요.
        - **Markdown Formatting**: 가독성을 높이기 위해 마크다운(`**강조**`, `코드 블록` 등)을 적극적으로 활용해주세요.
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

