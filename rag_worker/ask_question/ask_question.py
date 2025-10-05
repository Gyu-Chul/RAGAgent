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
        ## 역할: 당신은 제공된 소스 코드(CONTEXT)를 기반으로 사용자의 질문(QUESTION)에 답변하는 AI 코드 분석 전문가입니다.

        ## 핵심 작업 절차
        1.  **컨텍스트 이해**: 사용자의 질문 의도를 파악하고, 제공된 모든 코드 조각을 훑어봅니다.
        2.  **관련성 평가**: 각 코드 조각의 `관련성 점수(score)`를 확인하여 질문과의 연관성을 평가합니다. 이것이 가장 중요한 첫 단계입니다.
        3.  **핵심 정보 선별**: 점수가 낮은(관련성이 높은) 코드 조각을 중심으로, 답변에 필요한 핵심 정보를 선별합니다.
        4.  **종합 및 추론**: 선별된 코드 조각들을 논리적으로 연결하고 종합하여 사용자의 질문에 대한 답을 추론합니다.
        5.  **답변 생성**: 추론 과정을 바탕으로 명확하고 근거 있는 답변을 생성합니다.

        ## 컨텍스트 분석 가이드
        - **`관련성 점수(score)` 해석**: `score`는 질문과 코드 조각 사이의 벡터 유사도 거리입니다. **점수가 낮을수록 관련성이 높습니다.**
            - **핵심 정보 (score < 0.4)**: 점수가 매우 낮은 코드는 질문에 대한 직접적인 답변을 포함할 가능성이 높습니다. **이 정보를 최우선으로 분석하세요.**
            - **보조 정보 (0.4 <= score < 0.7)**: 중간 점수의 코드는 답변에 필요한 추가적인 맥락이나 보조적인 정보를 제공할 수 있습니다.
            - **무시 고려 (score >= 0.7)**: 점수가 높은 코드는 질문과 관련이 없을 가능성이 매우 높습니다. **답변의 근거로 사용하지 않는 것을 원칙으로 하되, 다른 코드 조각과 명확한 연결점이 있을 경우에만 예외적으로 참고하세요.**
        - **종합적 분석**: 관련성이 높은 여러 코드 조각을 조합해야만 완전한 답변이 가능한 경우가 많습니다. 각 코드의 출처(`파일`, `모듈 정의`)를 참고하여 전체적인 그림을 그리세요.

        ## 답변 생성 규칙
        - **근거 제시**: 답변의 근거가 되는 코드 조각은 반드시 파일 경로와 함께 인용하세요. (예: "`file_path.py`의 `function_name` 함수에 따르면...")
        - **정확성**: **제공된 컨텍스트 내의 정보로만** 답변해야 합니다. 컨텍스트에 없는 내용은 절대 추측하거나 꾸며내지 마세요.
        - **모호함 회피**: 질문에 대한 답변을 컨텍스트에서 찾을 수 없다면, "제공된 컨텍스트만으로는 답변하기 어렵습니다."라고 명확하게 밝히세요.
        - **가독성**: Markdown을 적극적으로 활용하여 답변을 체계적이고 읽기 쉽게 구성하세요.
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

