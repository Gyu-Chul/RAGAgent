from typing import List, Dict, Any
from langchain_core.runnables import RunnableSerializable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompt_values import ChatPromptValue

class DocsFormatter(RunnableSerializable):
    """
    검색 결과(List[Dict])를 입력받아
    LLM에게 전달할 단일 문자열(context)로 변환하는 Runnable 클래스.
    """
    def invoke(self, docs: List[Dict[str, Any]], config=None) -> str:
        if not docs:
            return "참고할 컨텍스트를 찾지 못했습니다."
        
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

# --------------------------------------------------------------------

def create_final_prompt(docs: List[Dict[str, Any]], query: str) -> ChatPromptValue:
    """
    검색 결과와 사용자 질문을 받아 최종 프롬프트 객체를 생성하는 함수.

    Args:
        docs (List[Dict[str, Any]]): 벡터 DB에서 검색된 문서 리스트.
        query (str): 사용자의 원본 질문.

    Returns:
        ChatPromptValue: LLM에 바로 전달할 수 있는 최종 프롬프트 객체.
    """
    # 1. 문서 포맷팅
    # DocsFormatter를 함수 내부에서 인스턴스화하여 사용합니다.
    formatter = DocsFormatter()
    formatted_context = formatter.invoke(docs)

    # 2. 프롬프트 템플릿 정의
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

    # 3. 템플릿 결합 및 최종 프롬프트 생성
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template),
    ])

    final_prompt = prompt_template.invoke({
        "context": formatted_context,
        "question": query
    })

    return final_prompt