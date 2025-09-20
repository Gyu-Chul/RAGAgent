import time, json, os, torch
from typing import List, Dict, Any

from langchain_community.vectorstores import Milvus
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings 
import config

# --- 1. 임베딩 체인 (Embedding Chain) ---

class EmbeddingInput(BaseModel):
    """임베딩 체인의 입력 모델"""
    json_path: str = Field(description="데이터가 담긴 JSON 파일 경로")
    collection_name: str = Field(description="저장할 Milvus 컬렉션 이름")
    model_name: str = Field(default=config.DEFAULT_EMBEDDING_MODEL, description="사용할 임베딩 모델")

def _embedding_process(input_data: EmbeddingInput) -> Dict[str, Any]:
    """JSON 파일을 읽어 Milvus에 임베딩하고 저장하는 로직"""
    print(f"\n▶️ 임베딩 시작: [Collection: {input_data.collection_name}, Model: {input_data.model_name}]")
    start_time = time.time()

    if not os.path.exists(input_data.json_path):
        return {"error": f"파일을 찾을 수 없음: {input_data.json_path}"}
    with open(input_data.json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceEmbeddings(
        model_name=input_data.model_name,
        model_kwargs={'device': device}
    )

    print(f"임베딩 모델 로드 완료. {len(items)}개 문서 처리 중...")
    
    Milvus.from_texts(
        texts=[json.dumps(item, ensure_ascii=False) for item in items],
        embedding=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI},
        primary_field="pk",
        text_field="text",
        vector_field="vector"
    )
    
    elapsed = time.time() - start_time
    return {
        "success": True,
        "message": f"🎉 {len(items)}개 문서 임베딩 완료! (⏱️ {elapsed:.2f}초 소요)"
    }

embedding_chain = RunnableLambda(_embedding_process)

# --- 2. 검색 체인 (Search Chain) ---

class SearchInput(BaseModel):
    """검색 체인의 입력 모델"""
    query: str
    collection_name: str
    model_name: str = Field(default=config.DEFAULT_EMBEDDING_MODEL)
    top_k: int = 3
    filter_expression: str | None = None

def _search_process(input_data: SearchInput) -> List[Dict[str, Any]]:
    """Milvus에서 벡터 검색을 수행하는 로직"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceEmbeddings(
        model_name=input_data.model_name,
        model_kwargs={'device': device}
    )
    
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI},
        primary_field="pk",
        text_field="text",
        vector_field="vector"
    )
    
    search_kwargs = {"k": input_data.top_k}
    if input_data.filter_expression:
        search_kwargs["expr"] = input_data.filter_expression
        
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    
    return retriever.invoke(input_data.query)

def format_docs(docs: List[Any]) -> str:
    """검색 결과를 사람이 보기 좋은 형태로 포맷팅"""
    if not docs:
        return "검색 결과가 없습니다."
    
    formatted_list = []
    for i, doc in enumerate(docs):
        formatted_list.append(
            f"  [{i+1}] 내용: {doc.page_content[:200]}..."
        )
    return "\n".join(formatted_list)

search_chain = RunnableLambda(_search_process)