import time, json, os, torch
from typing import List, Dict, Any, Literal

from langchain_community.vectorstores import Milvus
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import config
from db_utils import client # MilvusClient 직접 사용을 위해 import

# --- 1. 임베딩 체인 (Embedding Chain) ---

class EmbeddingInput(BaseModel):
    """임베딩 체인의 입력 모델"""
    json_path: str = Field(description="데이터가 담긴 JSON 파일 경로")
    collection_name: str = Field(description="저장할 Milvus 컬렉션 이름")
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY, description="config.py에 정의된 모델 키")

def _embedding_process(input_data: EmbeddingInput) -> Dict[str, Any]:
    print(f"\n▶️ 임베딩 시작: [Collection: {input_data.collection_name}, Model Key: {input_data.model_key}]")
    start_time = time.time()

    # --- 동적 모델 설정 로드 ---
    model_config = config.EMBEDDING_MODELS.get(input_data.model_key)
    if not model_config:
        return {"error": f"설정 파일에 없는 모델 키입니다: {input_data.model_key}"}
    
    model_name = model_config["model_name"]
    model_kwargs = model_config["kwargs"]
    # ---------------------------

    if not os.path.exists(input_data.json_path):
        return {"error": f"파일을 찾을 수 없음: {input_data.json_path}"}
    with open(input_data.json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model_kwargs['device'] = device
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs
    )

    print(f"임베딩 모델 로드 완료. {len(items)}개 문서 처리 중...")
    
    Milvus.from_texts(
        texts=[json.dumps(item, ensure_ascii=False) for item in items],
        embedding=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI}
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
    # 👇 검색 모드 추가
    search_mode: Literal["hybrid", "vector", "bm25"] = Field(
        default="hybrid", 
        description="검색 모드 선택"
    )
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY)
    top_k: int = 3
    filter_expression: str | None = None

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

def _search_process(input_data: SearchInput) -> List[Dict[str, Any]]:
    """선택된 검색 모드에 따라 Milvus에서 검색을 수행하는 로직"""
    print(f"\n▶️ 검색 시작: [Mode: {input_data.search_mode}, Collection: {input_data.collection_name}]")
    
    # --- 1. Dense Retriever (벡터 검색) 준비 ---
    model_config = config.EMBEDDING_MODELS[input_data.model_key]
    embeddings = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs=model_config["kwargs"]
    )
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=input_data.collection_name,
        connection_args={"uri": config.MILVUS_URI},
    )
    dense_retriever = vector_store.as_retriever(search_kwargs={"k": input_data.top_k})

    # --- 2. Sparse Retriever (BM25) 준비 (필요 시) ---
    if input_data.search_mode in ["hybrid", "bm25"]:
        # BM25는 메모리 기반이므로, Milvus에서 모든 문서를 가져와야 합니다.
        print("BM25 인덱싱을 위해 모든 문서를 로드합니다...")
        all_docs = get_all_docs_from_collection(input_data.collection_name)
        if not all_docs:
            print("⚠️ BM25 인덱싱할 문서가 없습니다. 벡터 검색만 수행합니다.")
            if input_data.search_mode == "bm25": return []
            return dense_retriever.invoke(input_data.query)
            
        sparse_retriever = BM25Retriever.from_texts(all_docs)
        sparse_retriever.k = input_data.top_k
    
    # --- 3. 검색 모드에 따라 Retriever 선택 및 실행 ---
    if input_data.search_mode == "hybrid":
        print("하이브리드 검색(Ensemble)을 수행합니다...")
        ensemble_retriever = EnsembleRetriever(
            retrievers=[dense_retriever, sparse_retriever], 
            weights=[0.5, 0.5] # 중요도 가중치, 조절 가능
        )
        return ensemble_retriever.invoke(input_data.query)

    elif input_data.search_mode == "bm25":
        print("BM25 단독 검색을 수행합니다...")
        return sparse_retriever.invoke(input_data.query)
        
    else: # "vector"
        print("벡터 단독 검색을 수행합니다...")
        return dense_retriever.invoke(input_data.query)

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