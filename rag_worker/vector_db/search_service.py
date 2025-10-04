"""
검색 처리 서비스
"""

import logging
import time
from typing import List, Dict, Any, Optional
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import AnnSearchRequest, RRFRanker

from .config import EMBEDDING_MODELS
from .collection_manager import MilvusConnectionManager
from .embedding_service import BM25ModelCache, DenseEmbedder
from .exceptions import SearchError, ModelLoadError
from .types import SearchInput, SearchResult, SearchResultItem

logger = logging.getLogger(__name__)


class SparseQueryEmbedder:
    """희소 쿼리 벡터 생성 클래스"""

    def __init__(self, collection_name: str) -> None:
        """
        SparseQueryEmbedder 초기화

        Args:
            collection_name: 컬렉션 이름

        Raises:
            ModelLoadError: BM25 모델을 찾을 수 없을 때
        """
        self.collection_name: str = collection_name
        self.bm25 = BM25ModelCache.get(collection_name)

        if self.bm25 is None:
            raise ModelLoadError(
                f"BM25 model not found for collection '{collection_name}'. "
                f"Please run embedding first."
            )

    def embed_query(self, query: str) -> Dict[int, float]:
        """
        쿼리를 희소 벡터로 변환

        Args:
            query: 검색 쿼리

        Returns:
            희소 벡터 (딕셔너리 형태)
        """
        tokenized_query = query.split(" ")
        doc_scores = self.bm25.get_scores(tokenized_query)
        sparse_vec = {i: score for i, score in enumerate(doc_scores) if score > 0}
        return sparse_vec


class SearchService:
    """검색 처리 통합 서비스 클래스"""

    def __init__(self) -> None:
        """SearchService 초기화"""
        self.client = MilvusConnectionManager.get_client()

    def search(self, input_data: SearchInput) -> SearchResult:
        """
        하이브리드 검색 수행 (밀집 + 희소 벡터)

        Args:
            input_data: 검색 입력

        Returns:
            검색 결과
        """
        start_time: float = time.time()

        try:
            logger.info(
                f"▶️ Starting hybrid search in collection: {input_data['collection_name']}"
            )

            # 1. 밀집 쿼리 벡터 생성
            logger.info("Generating dense query vector...")
            dense_vector = self._generate_dense_vector(
                input_data["query"], input_data["model_key"]
            )

            # 2. 희소 쿼리 벡터 생성
            logger.info("Generating sparse query vector (BM25)...")
            sparse_vector = self._generate_sparse_vector(
                input_data["query"], input_data["collection_name"]
            )

            # 3. 하이브리드 검색 수행
            logger.info("Executing hybrid search...")
            results = self._execute_hybrid_search(
                collection_name=input_data["collection_name"],
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                top_k=input_data["top_k"],
                filter_expr=input_data.get("filter_expr"),
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"✅ Search completed: {len(results)} results found in {elapsed_time:.2f}s"
            )

            return SearchResult(
                success=True,
                query=input_data["query"],
                collection_name=input_data["collection_name"],
                total_results=len(results),
                results=results,
                elapsed_time=elapsed_time,
                message=f"Found {len(results)} results",
                error=None,
            )

        except (ModelLoadError, SearchError, Exception) as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Search failed: {e}")

            return SearchResult(
                success=False,
                query=input_data.get("query", ""),
                collection_name=input_data.get("collection_name", ""),
                total_results=0,
                results=[],
                elapsed_time=elapsed_time,
                message=None,
                error=str(e),
            )

    def _generate_dense_vector(self, query: str, model_key: str) -> List[float]:
        """
        밀집 쿼리 벡터 생성

        Args:
            query: 검색 쿼리
            model_key: 모델 키

        Returns:
            밀집 벡터

        Raises:
            ModelLoadError: 모델 로드 실패 시
        """
        try:
            model_config = EMBEDDING_MODELS.get(model_key)
            if not model_config:
                raise ModelLoadError(f"Model config not found for key: {model_key}")

            device = "cuda" if torch.cuda.is_available() else "cpu"

            embedder = HuggingFaceEmbeddings(
                model_name=model_config["model_name"],
                model_kwargs={"device": device, "trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True},
            )

            return embedder.embed_query(query)

        except Exception as e:
            raise ModelLoadError(f"Failed to generate dense vector: {e}") from e

    def _generate_sparse_vector(
        self, query: str, collection_name: str
    ) -> Dict[int, float]:
        """
        희소 쿼리 벡터 생성

        Args:
            query: 검색 쿼리
            collection_name: 컬렉션 이름

        Returns:
            희소 벡터

        Raises:
            ModelLoadError: BM25 모델을 찾을 수 없을 때
        """
        sparse_embedder = SparseQueryEmbedder(collection_name)
        return sparse_embedder.embed_query(query)

    def _execute_hybrid_search(
        self,
        collection_name: str,
        dense_vector: List[float],
        sparse_vector: Dict[int, float],
        top_k: int,
        filter_expr: Optional[str] = None,
    ) -> List[SearchResultItem]:
        """
        하이브리드 검색 실행 (RRF 랭커 사용)

        Args:
            collection_name: 컬렉션 이름
            dense_vector: 밀집 쿼리 벡터
            sparse_vector: 희소 쿼리 벡터
            top_k: 결과 개수
            filter_expr: 필터 표현식 (선택)

        Returns:
            검색 결과 리스트

        Raises:
            SearchError: 검색 실패 시
        """
        try:
            # 밀집 벡터 검색 요청
            dense_req = AnnSearchRequest(
                data=[dense_vector],
                anns_field="dense",
                limit=top_k,
                param={"metric_type": "COSINE", "params": {"ef": 128}},
            )

            # 희소 벡터 검색 요청
            sparse_req = AnnSearchRequest(
                data=[sparse_vector],
                anns_field="sparse",
                limit=top_k,
                param={"metric_type": "IP"},
            )

            # 하이브리드 검색 실행
            search_params: Dict[str, Any] = {
                "collection_name": collection_name,
                "reqs": [dense_req, sparse_req],
                "ranker": RRFRanker(),
                "limit": top_k,
                "output_fields": ["*"],
            }

            # 필터 추가 (있을 경우)
            if filter_expr:
                search_params["filter"] = filter_expr

            res = self.client.hybrid_search(**search_params)

            if not res or not res[0]:
                return []

            # 결과 포맷팅
            return self._format_results(res[0])

        except Exception as e:
            raise SearchError(f"Hybrid search execution failed: {e}") from e

    def _format_results(self, hits: List[Any]) -> List[SearchResultItem]:
        """
        검색 결과를 포맷팅

        Args:
            hits: 검색 히트 리스트

        Returns:
            포맷팅된 결과 리스트
        """
        results: List[SearchResultItem] = []

        for hit in hits:
            fields = hit.entity.fields.copy()

            # 'text' -> 'code' 변환
            code = fields.pop("text", "")

            # 불필요한 필드 제거
            fields.pop("pk", None)
            fields.pop("dense", None)
            fields.pop("sparse", None)

            # 스코어 추가
            score = getattr(hit, "distance", None)

            result_item: SearchResultItem = SearchResultItem(
                code=code,
                file_path=fields.get("file_path", ""),
                name=fields.get("name", ""),
                start_line=fields.get("start_line", 0),
                end_line=fields.get("end_line", 0),
                type=fields.get("type", ""),
                _source_file=fields.get("_source_file", ""),
                score=score,
            )

            results.append(result_item)

        return results
