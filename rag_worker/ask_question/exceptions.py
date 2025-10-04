"""
LLM_API 예외 클래스 정의
"""


class LLMError(Exception):
    """LLM 모듈의 기본 예외 클래스"""

    pass

### prompt
class NoContextFoundError(LLMError):
    """컨텍스트로 사용할 검색된 문서가 없을 때 발생하는 예외"""
    pass

class PromptCreationError(LLMError):
    """프롬프트 템플릿을 채우는 중 오류가 발생했을 때"""
    
    pass

### ask_question
class ValueError(LLMError):
    """OPENAI_API_KEY를 찾을 수 없을 때 발생하는 예외"""

    pass


class UnsupportedModelError(LLMError):
    """지원하지 않는 모델을 요청했을 때 발생하는 예외"""

    pass


class LLMAPIError(LLMError):
    """OpenAI API 호출 중 문제가 발생했을 때 발생하는 예외"""

    pass
