"""
Vector DB 관련 타입 정의
"""

from typing import Dict, Any, List, Optional, Literal
from typing_extensions import TypedDict


class EmbeddingModelConfig(TypedDict):
    """임베딩 모델 설정"""

    model_name: str
    dim: int
    kwargs: Dict[str, Any]


class EmbeddingInput(TypedDict):
    """임베딩 작업 입력"""

    json_path: str
    collection_name: str
    model_key: str


class EmbeddingResult(TypedDict):
    """임베딩 작업 결과"""

    success: bool
    collection_name: str
    total_documents: int
    inserted_count: int
    elapsed_time: float
    message: Optional[str]
    error: Optional[str]


class SearchInput(TypedDict):
    """검색 작업 입력"""

    query: str
    collection_name: str
    model_key: str
    top_k: int
    filter_expr: Optional[str]


class SearchResultItem(TypedDict):
    """검색 결과 아이템"""

    code: str
    file_path: str
    name: str
    start_line: int
    end_line: int
    type: str
    _source_file: str
    score: Optional[float]


class SearchResult(TypedDict):
    """검색 작업 결과"""

    success: bool
    query: str
    collection_name: str
    total_results: int
    results: List[SearchResultItem]
    elapsed_time: float
    message: Optional[str]
    error: Optional[str]


class CollectionInfo(TypedDict):
    """컬렉션 정보"""

    name: str
    num_entities: int
    description: str


class CollectionCreateInput(TypedDict):
    """컬렉션 생성 입력"""

    collection_name: str
    dim: int
    description: Optional[str]


class CollectionCreateResult(TypedDict):
    """컬렉션 생성 결과"""

    success: bool
    collection_name: str
    message: Optional[str]
    error: Optional[str]


class CollectionDeleteResult(TypedDict):
    """컬렉션 삭제 결과"""

    success: bool
    collection_name: str
    message: Optional[str]
    error: Optional[str]


class CollectionListResult(TypedDict):
    """컬렉션 목록 조회 결과"""

    success: bool
    collections: List[CollectionInfo]
    total: int
    error: Optional[str]
