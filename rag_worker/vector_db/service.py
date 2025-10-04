"""
Vector DB 통합 서비스
"""

import logging
from typing import List, Optional

from .collection_manager import CollectionManager
from .embedding_service import EmbeddingService
from .search_service import SearchService
from .repository_embedder import RepositoryEmbedder
from .types import (
    CollectionInfo,
    CollectionCreateResult,
    CollectionDeleteResult,
    EmbeddingInput,
    EmbeddingResult,
    SearchInput,
    SearchResult,
)

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    Vector DB 통합 서비스 클래스

    컬렉션 관리, 임베딩, 검색 기능을 통합하여 제공합니다.
    """

    def __init__(self, batch_size: int = 256) -> None:
        """
        VectorDBService 초기화

        Args:
            batch_size: 임베딩 시 배치 크기
        """
        self.collection_manager: CollectionManager = CollectionManager()
        self.embedding_service: EmbeddingService = EmbeddingService(batch_size=batch_size)
        self.search_service: SearchService = SearchService()
        self.repository_embedder: RepositoryEmbedder = RepositoryEmbedder()

        logger.info("✅ VectorDBService initialized")

    # ==================== 컬렉션 관리 ====================

    def create_collection(
        self, collection_name: str, dim: int, description: Optional[str] = None
    ) -> CollectionCreateResult:
        """
        컬렉션 생성

        Args:
            collection_name: 컬렉션 이름
            dim: 밀집 벡터 차원
            description: 컬렉션 설명

        Returns:
            생성 결과
        """
        return self.collection_manager.create_collection(collection_name, dim, description)

    def delete_collection(self, collection_name: str) -> CollectionDeleteResult:
        """
        컬렉션 삭제

        Args:
            collection_name: 컬렉션 이름

        Returns:
            삭제 결과
        """
        return self.collection_manager.delete_collection(collection_name)

    def list_collections(self) -> List[CollectionInfo]:
        """
        모든 컬렉션 목록 조회

        Returns:
            컬렉션 정보 리스트
        """
        return self.collection_manager.list_collections()

    def collection_exists(self, collection_name: str) -> bool:
        """
        컬렉션 존재 여부 확인

        Args:
            collection_name: 컬렉션 이름

        Returns:
            존재 여부
        """
        return self.collection_manager.exists(collection_name)

    def get_entity_count(self, collection_name: str) -> int:
        """
        컬렉션의 엔티티 수 조회

        Args:
            collection_name: 컬렉션 이름

        Returns:
            엔티티 수
        """
        return self.collection_manager.get_entity_count(collection_name)

    # ==================== 임베딩 ====================

    def embed_documents(
        self, json_path: str, collection_name: str, model_key: str
    ) -> EmbeddingResult:
        """
        JSON 파일의 문서를 임베딩하여 컬렉션에 저장

        Args:
            json_path: JSON 파일 경로
            collection_name: 저장할 컬렉션 이름
            model_key: 사용할 임베딩 모델 키

        Returns:
            임베딩 결과
        """
        input_data: EmbeddingInput = EmbeddingInput(
            json_path=json_path, collection_name=collection_name, model_key=model_key
        )

        return self.embedding_service.process_embedding(input_data)

    def embed_repository(
        self, repo_name: str, collection_name: str, model_key: str
    ) -> EmbeddingResult:
        """
        파싱된 레포지토리 전체를 임베딩하여 컬렉션에 저장

        Args:
            repo_name: 레포지토리 이름 (parsed_repository/{repo_name}/)
            collection_name: 저장할 컬렉션 이름
            model_key: 사용할 임베딩 모델 키

        Returns:
            임베딩 결과
        """
        return self.repository_embedder.embed_repository(repo_name, collection_name, model_key)

    # ==================== 검색 ====================

    def search(
        self,
        query: str,
        collection_name: str,
        model_key: str,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
    ) -> SearchResult:
        """
        하이브리드 검색 수행

        Args:
            query: 검색 쿼리
            collection_name: 검색할 컬렉션 이름
            model_key: 사용할 임베딩 모델 키
            top_k: 반환할 결과 개수
            filter_expr: 필터 표현식 (선택)

        Returns:
            검색 결과
        """
        input_data: SearchInput = SearchInput(
            query=query,
            collection_name=collection_name,
            model_key=model_key,
            top_k=top_k,
            filter_expr=filter_expr,
        )

        return self.search_service.search(input_data)
