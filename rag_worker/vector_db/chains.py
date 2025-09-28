import time, json, os, torch
from typing import List, Any, Literal

from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_core.runnables import RunnableLambda
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi
from pydantic import BaseModel, Field

import config
from db_utils import client # MilvusClient 직접 사용을 위해 import

# --- 1. 임베딩 체인 (Embedding Chain) ---

class EmbeddingInput(BaseModel):
    """임베딩 체인의 입력 모델"""
    json_path: str = Field(description="데이터가 담긴 JSON 파일 경로")
    collection_name: str = Field(description="저장할 Milvus 컬렉션 이름")
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY, description="config.py에 정의된 모델 키")

def _embedding_process(input_data: EmbeddingInput) -> dict:
    print(f"\n▶️ 임베딩 시작 : [Collection: {input_data.collection_name}]")
    start_time = time.time()

    # --- 1. 데이터 로딩 및 준비 ---
    if not os.path.exists(input_data.json_path):
        return {"error": f"파일을 찾을 수 없음: {input_data.json_path}"}
    with open(input_data.json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    texts_to_embed = []
    metadata_list = []
    for item in items:
        page_content = item.get("code")
        if page_content and page_content.strip():   # code 영역이 비어있지 않는지 확인
            texts_to_embed.append(page_content)
            metadata_list.append({k: v for k, v in item.items() if k != "code"})

    if not texts_to_embed:
        return {"error": "JSON 파일에서 유효한 문서를 찾을 수 없습니다."}

    # --- 2. 밀집 벡터 생성 (LangChain 사용) ---
    print(f"{len(texts_to_embed)}개 문서에 대한 밀집 벡터 생성 중...")
    model_config = config.EMBEDDING_MODELS.get(input_data.model_key)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n사용 디바이스 : {device}")
    dense_embedder = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs={'device': device, 'trust_remote_code': True},
        encode_kwargs={"normalize_embeddings": True}
    )
    dense_vectors = dense_embedder.embed_documents(texts_to_embed)

    # --- 3. 희소 벡터 생성 (rank_bm25 직접 사용) ---
    print("희소 벡터 생성 중...")
    tokenized_corpus = [doc.split(" ") for doc in texts_to_embed]  # 개별 단어 기반을 위해 분리
    bm25 = BM25Okapi(tokenized_corpus)
    # 각 문서 자체를 쿼리로 사용하여 토큰별 가중치를 얻어 희소 벡터를 구성합니다.
    sparse_vectors = []
    for doc_tokens in tokenized_corpus:
        doc_scores = bm25.get_scores(doc_tokens)
        sparse_vec = {i: score for i, score in enumerate(doc_scores) if score > 0}
        sparse_vectors.append(sparse_vec)
    
    ### Vector 생성은 이미 끝
    ### 그것을 Milvus에 넣는 작업


    # --- 4. Milvus 삽입을 위한 데이터 패킷 조립 ---
    print("Milvus 삽입용 데이터 패킷 조립 중...")
    data_to_insert = []
    for i in range(len(texts_to_embed)):
        row = metadata_list[i].copy()       # 벡터화 되지 않는 나머지 메타데이터 리스트 삽입
        row["text"] = texts_to_embed[i]     # code 스키마 'text'
        row["dense"] = dense_vectors[i]     # dense vector 스키마 필드명 'dense'
        row["sparse"] = sparse_vectors[i]   # sparse vector 스키마 필드명 'sparse'
        data_to_insert.append(row)

    # --- 5. PyMilvus Client로 직접 데이터 삽입 ---
    try:
        print(f"PyMilvus 클라이언트로 데이터 {len(data_to_insert)}개 삽입 시도...")
        res = client.insert(
            collection_name=input_data.collection_name,
            data=data_to_insert
        )
        print(f"✅ 데이터 삽입 성공! Inserted Count: {res['insert_count']}")

    except Exception as e:
        print(f"❌ 데이터 삽입 중 심각한 오류 발생: {e}")
        return {"error": f"데이터 삽입 오류: {e}"}

    elapsed = time.time() - start_time
    return {"success": True, "message": f"🎉 {len(texts_to_embed)}개 문서 임베딩 및 삽입 완료! (⏱️ {elapsed:.2f}초 소요)"}

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