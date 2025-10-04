"""
Vector DB 패키지
"""

from .service import VectorDBService
from .collection_manager import CollectionManager, MilvusConnectionManager
from .embedding_service import EmbeddingService, BM25ModelCache, DenseEmbedder, SparseEmbedder
from .search_service import SearchService, SparseQueryEmbedder
from .repository_embedder import RepositoryEmbedder
from .types import (
    EmbeddingModelConfig,
    EmbeddingInput,
    EmbeddingResult,
    SearchInput,
    SearchResult,
    SearchResultItem,
    CollectionInfo,
    CollectionCreateInput,
    CollectionCreateResult,
    CollectionDeleteResult,
    CollectionListResult,
)
from .exceptions import (
    VectorDBError,
    CollectionNotFoundError,
    CollectionAlreadyExistsError,
    EmbeddingError,
    SearchError,
    ConnectionError,
    DataValidationError,
    ModelLoadError,
)
from .config import EMBEDDING_MODELS, DEFAULT_MODEL_KEY, MILVUS_URI

__all__ = [
    # Main Service
    "VectorDBService",
    # Service Components
    "CollectionManager",
    "MilvusConnectionManager",
    "EmbeddingService",
    "BM25ModelCache",
    "DenseEmbedder",
    "SparseEmbedder",
    "SearchService",
    "SparseQueryEmbedder",
    "RepositoryEmbedder",
    # Types
    "EmbeddingModelConfig",
    "EmbeddingInput",
    "EmbeddingResult",
    "SearchInput",
    "SearchResult",
    "SearchResultItem",
    "CollectionInfo",
    "CollectionCreateInput",
    "CollectionCreateResult",
    "CollectionDeleteResult",
    "CollectionListResult",
    # Exceptions
    "VectorDBError",
    "CollectionNotFoundError",
    "CollectionAlreadyExistsError",
    "EmbeddingError",
    "SearchError",
    "ConnectionError",
    "DataValidationError",
    "ModelLoadError",
    # Config
    "EMBEDDING_MODELS",
    "DEFAULT_MODEL_KEY",
    "MILVUS_URI",
]
