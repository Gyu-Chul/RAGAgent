import time, json, os, torch
from typing import List, Dict, Any, Literal

from langchain_core.documents import Document
from langchain_community.vectorstores import Milvus
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_milvus import BM25BuiltInFunction
import config
from db_utils import client # MilvusClient 직접 사용을 위해 import

# --- 1. 임베딩 체인 (Embedding Chain) ---

class EmbeddingInput(BaseModel):
    """임베딩 체인의 입력 모델"""
    json_path: str = Field(description="데이터가 담긴 JSON 파일 경로")
    collection_name: str = Field(description="저장할 Milvus 컬렉션 이름")
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY, description="config.py에 정의된 모델 키")

def _embedding_process(input_data: EmbeddingInput) -> Dict[str, Any]:
    print(f"\n▶️ 네이티브 임베딩 시작: [Collection: {input_data.collection_name}]")
    start_time = time.time()

    model_config = config.EMBEDDING_MODELS.get(input_data.model_key)
    if not model_config: return {"error": f"없는 모델 키: {input_data.model_key}"}

    if not os.path.exists(input_data.json_path):
        return {"error": f"파일을 찾을 수 없음: {input_data.json_path}"}
    with open(input_data.json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    # --- 👇 데이터를 LangChain Document 객체로 변환 ---
    docs = [Document(page_content=json.dumps(item, ensure_ascii=False)) for item in items]
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_kwargs = model_config["kwargs"]
    model_kwargs['device'] = device
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": True} # COSINE 유사도를 위해 정규화
    )

    print(f"임베딩 및 데이터 삽입 중... (밀집/희소 벡터 동시 생성)")
    
    # --- 👇 from_documents와 BM25BuiltInFunction 사용 ---
    Milvus.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI},
        # 희소 벡터 자동 생성을 위한 설정
        builtin_function=BM25BuiltInFunction(), 
        # 스키마의 필드 이름과 매핑
        vector_field="dense_vector",
        sparse_vector_field="sparse_vector",
        text_field="text",
        primary_field="pk"
    )
    
    elapsed = time.time() - start_time
    return {"success": True, "message": f"🎉 {len(docs)}개 문서 임베딩 완료! (⏱️ {elapsed:.2f}초 소요)"}

embedding_chain = RunnableLambda(_embedding_process)

# --- 2. 검색 체인 (Search Chain) ---

class SearchInput(BaseModel):
    query: str
    collection_name: str
    search_mode: Literal["hybrid", "vector", "bm25"] = "hybrid"
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY)
    top_k: int = 3

def get_all_docs_from_collection(collection_name: str) -> List[str]:
    """Milvus 컬렉션에서 모든 'text' 필드 문서를 가져옵니다. (BM25 인덱싱용)"""
    if not client.has_collection(collection_name):
        return []
    # Milvus는 모든 데이터를 한 번에 가져오는 직접적인 방법이 제한적이므로
    # 여기서는 ID를 기반으로 반복 조회하는 방식을 사용합니다.
    # 대규모 데이터셋에서는 이 부분을 최적화해야 합니다.
    try:
        # 컬렉션의 엔티티 수를 먼저 확인
        count = client.get_collection_stats(collection_name).get("row_count", 0)
        # 모든 ID를 조회하여 데이터를 가져옴
        results = client.query(
            collection_name=collection_name,
            filter="",
            output_fields=["text"],
            limit=int(count) if count > 0 else 10000 # count가 0일 경우 대비
        )
        return [res["text"] for res in results]
    except Exception as e:
        print(f"컬렉션 문서 조회 중 오류: {e}")
        return []

def _search_process(input_data: SearchInput) -> List[Document]:
    print(f"\n▶️ 네이티브 검색 시작: [Mode: {input_data.search_mode}]")
    
    model_config = config.EMBEDDING_MODELS[input_data.model_key]
    embeddings = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs=model_config["kwargs"],
        encode_kwargs={"normalize_embeddings": True}
    )
    
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI},
        vector_field="dense_vector",
        sparse_vector_field="sparse_vector",
        text_field="text",
        primary_field="pk"
    )
    
    # --- 👇 search_type을 이용해 네이티브 검색 모드 제어 ---
    search_type_map = {
        "hybrid": "hybrid",
        "vector": "similarity",
        "bm25": "sparse"
    }
    stype = search_type_map.get(input_data.search_mode, "hybrid")
    
    retriever = vector_store.as_retriever(
        search_type=stype,
        search_kwargs={"k": input_data.top_k}
    )
    
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