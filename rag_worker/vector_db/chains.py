import time, json, os, torch
from typing import List, Any, Dict

from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_core.runnables import RunnableLambda
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import AnnSearchRequest, RRFRanker
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

# --- BM25 모델을 저장하고 재사용하기 위한 인메모리 캐시 ---
bm25_models = {}

def get_bm25_model(collection_name: str) -> BM25Okapi:
    """컬렉션의 BM25 모델을 캐시에서 가져오거나, 없으면 새로 생성합니다."""
    if collection_name in bm25_models:
        return bm25_models[collection_name]

    print(f"  - 경고: BM25 모델이 캐시에 없습니다. '{collection_name}' 컬렉션 전체를 읽어 새로 생성합니다 (시간 소요).")
    all_docs_from_db = client.query(
        collection_name=collection_name, filter="", output_fields=["text"], limit=16384
    )
    corpus = [res['text'] for res in all_docs_from_db]
    if not corpus:
        return None
        
    tokenized_corpus = [doc.split(" ") for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_models[collection_name] = bm25 # 다음 사용을 위해 캐시에 저장
    return bm25


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



    # --- 2. 희소 벡터 생성 (rank_bm25 직접 사용) ---
    print("희소 벡터 생성 시작")

    tokenized_corpus = [doc.split(" ") for doc in texts_to_embed]  # 개별 단어 기반을 위해 분리
    bm25 = BM25Okapi(tokenized_corpus)

    bm25_models[input_data.collection_name] = bm25
    print("✅ BM25 모델 생성 및 캐싱 완료.")

    sparse_vectors = []
    for doc_tokens in tokenized_corpus:
        doc_scores = bm25.get_scores(doc_tokens)
        sparse_vec = {i: score for i, score in enumerate(doc_scores) if score > 0}
        sparse_vectors.append(sparse_vec)
    
    print("✅ 모든 희소 벡터 생성 완료")



    # --- 3. 밀집 벡터 생성 (LangChain 사용) ---
    print(f"{len(texts_to_embed)}개 밀집 벡터 생성 시작")
    model_config = config.EMBEDDING_MODELS.get(input_data.model_key)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n사용 디바이스 : {device}")

    dense_embedder = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs={'device': device, 'trust_remote_code': True},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    ## HuggingFaceEmbeddings 모델이 GPU 최적화 포함해서 벡터화 진행
    dense_vectors = dense_embedder.embed_documents(texts_to_embed)
    
    ### Vector 생성은 종료
    ### 그것을 Milvus에 넣는 작업 - Memory Management & Stable Data Transfer를 위한 배치 사이즈 조절

    # GPU 메모리에 맞춰 배치 사이즈 조절
    # VRAM ~8GB : 256     //  VRAM ~12GB : 512
    # VRAM ~16GB : 1024   //  VRAM 24GB~ : 2048 ~
    batch_size = 256
    inserted_count = 0

    for i in range(0, len(texts_to_embed), batch_size):
        batch_end = min(i + batch_size, len(texts_to_embed))
        print(f"  - 배치 처리 중: {i+1} ~ {batch_end} / {len(texts_to_embed)}")

        # 현재 배치에 해당하는 데이터 조립
        data_to_insert = []
        for j in range(i, batch_end):
            row = metadata_list[j].copy()
            row["text"] = texts_to_embed[j]
            row["dense"] = dense_vectors[j] 
            row["sparse"] = sparse_vectors[j]
            data_to_insert.append(row)

        # 배치 단위로 데이터 삽입
        try:
            res = client.insert(
                collection_name=input_data.collection_name,
                data=data_to_insert
            )
            inserted_count += res['insert_count']
            print(f"  ✅ 배치 삽입 성공! (총 {inserted_count}개 삽입)")
        except Exception as e:
            print(f"❌ 배치 삽입 중 오류 발생: {e}")
            return {"error": f"배치 {i} 삽입 중 오류: {e}"}

    elapsed = time.time() - start_time
    return {"success": True, "message": f"🎉 {len(texts_to_embed)}개 문서 임베딩 및 삽입 완료! (⏱️ {elapsed:.2f}초 소요)"}

embedding_chain = RunnableLambda(_embedding_process)

# --- 2. 검색 체인 (Search Chain) ---

class SearchInput(BaseModel):
    query: str
    collection_name: str
    ## search_mode: Literal["hybrid", "vector", "bm25"] = "hybrid"
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY)
    top_k: int = 5

def _search_process(input_data: SearchInput) -> List[Dict[str, Any]]:
    """MilvusClient의 hybrid_search를 사용하여 검색을 수행합니다."""
    print(f"\n▶️ 하이브리드 검색 시작 (MilvusClient 방식): [Collection: {input_data.collection_name}]")
    
    collection_name = input_data.collection_name
    query = input_data.query
    top_k = input_data.top_k
    
    # --- 1. 밀집/희소 쿼리 벡터 생성 ---
    # 밀집 쿼리 벡터 생성
    print("  - 밀집 쿼리 벡터 생성 중...")
    model_config = config.EMBEDDING_MODELS[input_data.model_key]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dense_embedder = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs={'device': device, 'trust_remote_code': True}
    )
    query_dense_vector = dense_embedder.embed_query(query)
    
    # --- 희소 쿼리 벡터 생성 ---
    print("  - BM25 모델을 사용하여 희소 쿼리 벡터 생성 중...")
    bm25 = get_bm25_model(collection_name)
    if bm25 is None:
        print("  - 오류: 희소 벡터 모델을 생성할 수 없어 검색을 중단합니다.")
        return []

    tokenized_query = query.split(" ")
    # 쿼리의 토큰별 가중치를 계산하여 희소 벡터 생성
    doc_scores = bm25.get_scores(tokenized_query)
    query_sparse_vector = {i: score for i, score in enumerate(doc_scores) if score > 0}
    
    # --- 2. 각 벡터 필드에 대한 검색 요청(AnnSearchRequest) 생성 ---
    print("  - 밀집/희소 검색 요청 생성 중...")

    # 밀집 벡터 검색 요청
    dense_req = AnnSearchRequest(
        data=[query_dense_vector],
        anns_field="dense",
        limit=top_k,
        param={"metric_type": "COSINE", "params": {"ef": 128}}
    )

    # 희소 벡터 검색 요청
    sparse_req = AnnSearchRequest(
        data=[query_sparse_vector], # 텍스트 쿼리를 직접 전달
        anns_field="sparse",
        limit=top_k,
        param={"metric_type": "IP"}
    )

    # --- 3. RRF 랭커를 사용하여 hybrid_search 실행 ---
    print("  - client.hybrid_search 로 RRF 조합 검색 실행...")
    res = client.hybrid_search(
        collection_name=collection_name,
        reqs=[dense_req, sparse_req],
        ranker=RRFRanker(),
        limit=top_k,
        output_fields=["*"]
    )

    if not res or not res[0]:
        return []

    print("  - 검색 결과를 최종 JSON 구조로 포맷팅 중...")
    final_results = []
    for hit in res[0]:
        result_item = hit.entity.fields.copy()
        
        # 'text' 필드 -> 'code'
        result_item['code'] = result_item.pop('text', '')
        
        # 불필요한 필드 제거
        result_item.pop('pk', None)
        result_item.pop('dense', None)
        result_item.pop('sparse', None)
        
        final_results.append(result_item)
    
    return final_results



search_chain = RunnableLambda(_search_process)
