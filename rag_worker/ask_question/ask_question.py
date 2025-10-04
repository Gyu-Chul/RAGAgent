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
        ## 역할(Role)
        당신은 소스 코드 분석을 전문으로 하는 AI 기술 전문가입니다.

        ## 임무(Mission)
        당신의 임무는 주어진 '컨텍스트'의 코드 조각들을 깊이 분석하여, 사용자의 '질문'에 대해 정확하고 상세하며 개발자가 이해하기 쉬운 답변을 제공하는 것입니다.

        ## 가장 중요한 규칙(Golden Rule)
        - 답변은 **반드시** 주어진 '컨텍스트'의 코드 내용에만 근거해야 합니다. 당신의 사전 지식이나 외부 정보를 절대 사용해서는 안 됩니다.
        - '컨텍스트'에 답변의 근거가 없다면, **절대** 추측해서 답변하지 마세요. 이 경우, "주어진 컨텍스트만으로는 질문에 답변할 수 없습니다."라고 솔직하게 말해야 합니다.

        ## 답변 스타일(Style)
        - 어떤 파일의 어떤 함수나 클래스를 참고했는지 출처를 밝히며 설명해주세요.
        - 답변 내용에 연관된 코드 조각을 예시로 포함하여 이해를 도와주세요.
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

