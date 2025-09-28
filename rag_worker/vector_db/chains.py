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



    # --- 2. 희소 벡터 생성 (rank_bm25 직접 사용) ---
    print("희소 벡터 생성 시작")

    tokenized_corpus = [doc.split(" ") for doc in texts_to_embed]  # 개별 단어 기반을 위해 분리
    bm25 = BM25Okapi(tokenized_corpus)

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
    search_mode: Literal["hybrid", "vector", "bm25"] = "hybrid"
    model_key: str = Field(default=config.DEFAULT_MODEL_KEY)
    top_k: int = 3

def reciprocal_rank_fusion(results: List[List[Document]], k: int = 60) -> List[Document]:
    """Reciprocal Rank Fusion (RRF) 알고리즘을 사용하여 여러 검색 결과를 조합합니다."""
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_content = doc.page_content # Document 객체의 내용을 키로 사용
            if doc_content not in fused_scores:
                fused_scores[doc_content] = {"score": 0, "doc": doc}
            fused_scores[doc_content]["score"] += 1 / (rank + k)

    reranked_results = sorted(fused_scores.values(), key=lambda x: x["score"], reverse=True)
    return [item["doc"] for item in reranked_results]


def _search_process(input_data: SearchInput) -> List[Document]:
    print(f"\n▶️ 하이브리드 검색 시작 (수동 방식): [Mode: {input_data.search_mode}]")
    
    collection_name = input_data.collection_name
    query = input_data.query
    top_k = input_data.top_k
    
    # --- 1. 밀집/희소 벡터 생성을 위한 모델 준비 ---
    model_config = config.EMBEDDING_MODELS[input_data.model_key]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    dense_embedder = HuggingFaceEmbeddings(
        model_name=model_config["model_name"],
        model_kwargs={'device': device, 'trust_remote_code': True},
        encode_kwargs={"normalize_embeddings": True}
    )

    # --- 2. 검색 모드에 따른 분기 처리 ---
    
    # 2-1. 밀집 벡터 검색 (Dense Search)
    if input_data.search_mode in ["dense", "hybrid"]:
        print("  - 밀집 벡터로 의미 검색 실행...")
        query_dense_vector = dense_embedder.embed_query(query)
        
        dense_search_params = {"metric_type": "COSINE", "params": {"ef": 128}}
        dense_results = client.search(
            collection_name=collection_name,
            data=[query_dense_vector],
            anns_field="dense", # 스키마 필드명
            limit=top_k,
            search_params=dense_search_params,
            output_fields=["*"] # 모든 메타데이터 포함
        )
    
    # 2-2. 희소 벡터 검색 (Sparse Search)
    if input_data.search_mode in ["sparse", "hybrid"]:
        print("  - 희소 벡터로 키워드 검색 실행...")
        # 쿼리를 희소 벡터로 변환 (임베딩 시와 동일한 로직 필요)
        # 이 부분은 실제 서비스에서는 전체 코퍼스로 만든 BM25 모델을 재사용해야 합니다.
        # 여기서는 임시로 간단하게 구현합니다.
        temp_corpus = [query] # 임시 코퍼스
        tokenized_query = [doc.split(" ") for doc in temp_corpus]
        bm25 = BM25Okapi(tokenized_query)
        query_sparse_vector = {i: score for i, score in enumerate(bm25.get_scores(tokenized_query[0])) if score > 0}

        sparse_search_params = {"metric_type": "IP"}
        sparse_results = client.search(
            collection_name=collection_name,
            data=[query_sparse_vector],
            anns_field="sparse", # 스키마 필드명
            limit=top_k,
            search_params=sparse_search_params,
            output_fields=["*"]
        )

    # --- 3. 검색 결과 조합 및 반환 ---
    final_docs = []
    
    if input_data.search_mode == "dense":
        print("✅ 밀집 벡터 검색 결과 반환")
        # Pymilvus 결과를 LangChain Document로 변환
        hits = dense_results[0]
        final_docs = [Document(page_content=hit['entity'].get('text', ''), metadata={k:v for k,v in hit['entity'].items() if k != 'text'}) for hit in hits]

    elif input_data.search_mode == "sparse":
        print("✅ 희소 벡터 검색 결과 반환")
        hits = sparse_results[0]
        final_docs = [Document(page_content=hit['entity'].get('text', ''), metadata={k:v for k,v in hit['entity'].items() if k != 'text'}) for hit in hits]
    
    elif input_data.search_mode == "hybrid":
        print("✅ 하이브리드 검색 결과 조합 (RRF)...")
        dense_hits = [Document(page_content=hit['entity'].get('text', ''), metadata={k:v for k,v in hit['entity'].items() if k != 'text'}) for hit in dense_results[0]]
        sparse_hits = [Document(page_content=hit['entity'].get('text', ''), metadata={k:v for k,v in hit['entity'].items() if k != 'text'}) for hit in sparse_results[0]]
        
        # RRF 알고리즘으로 두 결과 랭킹 조합
        final_docs = reciprocal_rank_fusion([dense_hits, sparse_hits])
        final_docs = final_docs[:top_k] # 최종 top_k 개수만큼 자르기

    return final_docs

def format_docs(docs: List[Document]) -> str:
    # ... (기존 format_docs 함수는 그대로 사용 가능) ...
    # metadata도 함께 보여주도록 개선하면 좋습니다.
    if not docs:
        return "검색 결과가 없습니다."
    
    formatted_list = []
    # for i, doc in enumerate(docs):
    #     # file_path 메타데이터가 있으면 함께 출력
    #     file_path = doc.metadata.get('file_path', 'N/A')
    #     formatted_list.append(
    #         f"  [{i+1}] 경로: {file_path}\n      내용: {doc.page_content[:200].replace(chr(10), ' ')}..."
    #     )
    return "\n".join(formatted_list)

search_chain = RunnableLambda(_search_process) | RunnableLambda(format_docs)




# def get_all_docs_from_collection(collection_name: str) -> List[str]:
#     """Milvus 컬렉션에서 모든 'text' 필드 문서를 가져옵니다. (BM25 인덱싱용)"""
#     if not client.has_collection(collection_name):
#         return []
#     # Milvus는 모든 데이터를 한 번에 가져오는 직접적인 방법이 제한적이므로
#     # 여기서는 ID를 기반으로 반복 조회하는 방식을 사용합니다.
#     # 대규모 데이터셋에서는 이 부분을 최적화해야 합니다.
#     try:
#         # 컬렉션의 엔티티 수를 먼저 확인
#         count = client.get_collection_stats(collection_name).get("row_count", 0)
#         # 모든 ID를 조회하여 데이터를 가져옴
#         results = client.query(
#             collection_name=collection_name,
#             filter="",
#             output_fields=["text"],
#             limit=int(count) if count > 0 else 10000 # count가 0일 경우 대비
#         )
#         return [res["text"] for res in results]
#     except Exception as e:
#         print(f"컬렉션 문서 조회 중 오류: {e}")
#         return []

# def _search_process(input_data: SearchInput) -> List[Document]:
#     print(f"\n▶️ 네이티브 검색 시작: [Mode: {input_data.search_mode}]")
    
#     model_config = config.EMBEDDING_MODELS[input_data.model_key]
#     embeddings = HuggingFaceEmbeddings(
#         model_name=model_config["model_name"],
#         model_kwargs=model_config["kwargs"],
#         encode_kwargs={"normalize_embeddings": True}
#     )
    
#     vector_store = Milvus(
#         embedding_function=embeddings,
#         collection_name=input_data.collection_name,
#         connection_args={"uri": config.MILVUS_URI},
#         vector_field="dense_vector",
#         sparse_vector_field="sparse_vector",
#         text_field="text",
#         primary_field="pk"
#     )
    
#     # --- 👇 search_type을 이용해 네이티브 검색 모드 제어 ---
#     search_type_map = {
#         "hybrid": "hybrid",
#         "vector": "similarity",
#         "bm25": "sparse"
#     }
#     stype = search_type_map.get(input_data.search_mode, "hybrid")
    
#     retriever = vector_store.as_retriever(
#         search_type=stype,
#         search_kwargs={"k": input_data.top_k}
#     )
    
#     return retriever.invoke(input_data.query)

# def format_docs(docs: List[Any]) -> str:
#     """검색 결과를 사람이 보기 좋은 형태로 포맷팅"""
#     if not docs:
#         return "검색 결과가 없습니다."
    
#     formatted_list = []
#     for i, doc in enumerate(docs):
#         formatted_list.append(
#             f"  [{i+1}] 내용: {doc.page_content[:200]}..."
#         )
#     return "\n".join(formatted_list)

# search_chain = RunnableLambda(_search_process)