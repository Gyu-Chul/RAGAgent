from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompt_values import ChatPromptValue

from .types import SearchResult
from .exceptions import NoContextFoundError, PromptCreationError


class PromptGenerator:
    """
    검색된 문서(context)와 질문(query)를 이용해
    LLM에 전달할 최종 프롬프트를 생성하는 클래스
    """

    system_prompt_template = """
    당신은 주어진 코드 컨텍스트를 바탕으로 질문에 답변하는 유용한 AI 어시스턴트입니다.
    당신의 임무는 주어진 소스 코드 조각들을 분석하여 사용자의 질문에 포괄적이고 정확한 답변을 제공하는 것입니다.
    만약 주어진 컨텍스트에서 답변을 찾을 수 없다면, 정보를 지어내지 말고 명확하게 답변을 찾을 수 없다고 말해주세요.
    """
    human_prompt_template = """
    아래 코드 컨텍스트를 바탕으로 질문에 답변해 주세요.

    --- 컨텍스트 ---
    {context}
    --- 컨텍스트 종료 ---

    질문: {question}
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template),
    ])


    def _format_docs(self, docs: List[SearchResult]) -> str:
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
                    f"- 클래스: {doc.get('class_name', 'N/A')}\n"
                    f"- 함수: {doc.get('function_name', 'N/A')}"
                )
                code_block = f"```python\n{doc.get('code', '')}\n```"
                formatted_strings.append(f"{source_info}\n{code_block}")
            
            return "\n\n".join(formatted_strings)
        

        except (TypeError, AttributeError) as e:
            raise PromptCreationError(f"문서 포맷팅 중 오류 발생: 잘못된 데이터 구조. {e}") from e

    def create(self, docs: List[SearchResult], query: str) -> ChatPromptValue:
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
            final_prompt = self.prompt_template.invoke({
                "context": formatted_context,
                "question": query
            })
            return final_prompt
        except KeyError as e:
            raise PromptCreationError(f"프롬프트 템플릿 생성 실패: 필요한 키({e})가 없습니다.") from e


# class DocsFormatter(RunnableSerializable):
#     """
#     검색 결과(List[Dict])를 입력받아
#     LLM에게 전달할 단일 문자열(context)로 변환하는 Runnable 클래스.
#     """
#     def invoke(self, docs: List[Dict[str, Any]], config=None) -> str:
#         if not docs:
#             return "참고할 컨텍스트를 찾지 못했습니다."
        
#         formatted_strings = []
#         for i, doc in enumerate(docs):
#             source_info = (
#                 f"출처 {i+1}:\n"
#                 f"- 파일: {doc.get('file_path', 'N/A')}\n"
#                 f"- 클래스: {doc.get('class_name', 'N/A')}\n"
#                 f"- 함수: {doc.get('function_name', 'N/A')}"
#             )
#             code_block = f"```python\n{doc.get('code', '')}\n```"
#             formatted_strings.append(f"{source_info}\n{code_block}")
            
#         return "\n\n".join(formatted_strings)

# # --------------------------------------------------------------------

# def create_final_prompt(docs: List[Dict[str, Any]], query: str) -> ChatPromptValue:
#     """
#     검색 결과와 사용자 질문을 받아 최종 프롬프트 객체를 생성하는 함수.

#     Args:
#         docs (List[Dict[str, Any]]): 벡터 DB에서 검색된 문서 리스트.
#         query (str): 사용자의 원본 질문.

#     Returns:
#         ChatPromptValue: LLM에 바로 전달할 수 있는 최종 프롬프트 객체.
#     """
#     # 1. 문서 포맷팅
#     # DocsFormatter를 함수 내부에서 인스턴스화하여 사용합니다.
#     formatter = DocsFormatter()
#     formatted_context = formatter.invoke(docs)

#     # 2. 프롬프트 템플릿 정의
#     system_prompt_template = """
#     당신은 주어진 코드 컨텍스트를 바탕으로 질문에 답변하는 유용한 AI 어시스턴트입니다.
#     당신의 임무는 주어진 소스 코드 조각들을 분석하여 사용자의 질문에 포괄적이고 정확한 답변을 제공하는 것입니다.
#     만약 주어진 컨텍스트에서 답변을 찾을 수 없다면, 정보를 지어내지 말고 명확하게 답변을 찾을 수 없다고 말해주세요.
#     """
#     human_prompt_template = """
#     아래 코드 컨텍스트를 바탕으로 질문에 답변해 주세요.

#     --- 컨텍스트 ---
#     {context}
#     --- 컨텍스트 종료 ---

#     질문: {question}
#     """

#     # 3. 템플릿 결합 및 최종 프롬프트 생성
#     prompt_template = ChatPromptTemplate.from_messages([
#         ("system", system_prompt_template),
#         ("human", human_prompt_template),
#     ])

#     final_prompt = prompt_template.invoke({
#         "context": formatted_context,
#         "question": query
#     })

#     return final_prompt