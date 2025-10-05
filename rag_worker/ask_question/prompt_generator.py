from typing import List

from .types import SearchResultItem
from .exceptions import NoContextFoundError, PromptCreationError


class PromptGenerator:
    """
    검색된 문서(context)와 질문(query)를 이용해
    LLM에 전달할 최종 프롬프트를 생성하는 클래스
    """

    human_prompt_template = """
    아래 코드 컨텍스트를 바탕으로 질문에 답변해 주세요.

    --- 컨텍스트 ---
    {context}
    --- 컨텍스트 종료 ---

    질문: {question}
    """


    def _format_docs(self, docs: List[SearchResultItem]) -> str:
        """
        검색된 문서 리스트를 하나의 문자열 컨텍스트로 포맷팅
        
        Args:
            벡터 검색에서 나온 file_path, name, code str
        
        Return:
            포맷팅 된 하나의 str

        Raises:
            NoContextFoundError: docs input이 들어오지 않았을 때
            PromptCreationError: docs의 데이터 타입이 잘못되었을 때
        """
        if not docs:
            raise NoContextFoundError("컨텍스트로 사용할 검색된 문서가 없습니다.")
        

        try:
            formatted_strings = []
            for i, doc in enumerate(docs):
                source_info = (
                    f"출처 {i+1}:\n"
                    f"- 파일: {doc.get('file_path', 'N/A')}\n"
                    f"- 모듈 정의: {doc.get('type', 'unknown')} '{doc.get('name', 'N/A')}'\n"
                    f"- 관련성 점수: {doc.get('score', 'unknown')}"
                )
                code_block = f"```python\n{doc.get('code', '')}\n```"
                formatted_strings.append(f"{source_info}\n{code_block}")

            return "\n\n".join(formatted_strings)
        

        except (TypeError, AttributeError) as e:
            raise PromptCreationError(f"문서 포맷팅 중 오류 발생: 잘못된 데이터 구조. {e}") from e

    def create(self, docs: List[SearchResultItem], query: str) -> str:
        """
        포맷팅된 문서와 질문을 받아 최종 프롬프트 객체를 생성

        Args:
            docs: _format_docs 메서드를 통해 포맷팅된 코드 문서
            query: 사용자의 질문 str

        Return:
            완성된 prompt 객체

        Raies:
            PromptCreationError: 프롬프트 생성에 필요한 키가 없을 때
        """
        #_format_docs로 문서 포맷팅
        formatted_context = self._format_docs(docs)

        try:
            final_prompt = self.human_prompt_template.format(
                context=formatted_context,
                question=query
            )
            return str(final_prompt)
        except KeyError as e:
            raise PromptCreationError(f"프롬프트 템플릿 생성 실패: 필요한 키({e})가 없습니다.") from e

