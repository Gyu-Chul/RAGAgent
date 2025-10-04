import openai
import os
from dotenv import load_dotenv

from typing import List
from .types import LLMRequest, ChatMessage
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

    def ask_question(self, request: LLMRequest) -> str:
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
        # input 객체에서 파라미터 추출 (값이 없으면 기본값 사용)
        prompt = request['prompt']
        use_stream = request.get('use_stream', False)
        model = request.get('model', self.MODELS[0])
        temperature = request.get('temperature', 0.1)
        max_tokens = request.get('max_tokens', 1024)
        
        if model not in self.MODELS:
            # ❗ 오류 메시지를 반환하는 대신, 예외를 발생시킵니다.
            raise UnsupportedModelError(f"지원하지 않는 모델입니다: '{model}'. 지원 모델: {self.MODELS}")
        
        # API 호출
        messages: List[ChatMessage] = [
            {"role": "system", "content": "You are a helpful assistant."},
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

