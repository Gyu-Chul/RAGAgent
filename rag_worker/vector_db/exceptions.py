"""
Vector DB 관련 예외 정의
"""


class VectorDBError(Exception):
    """Vector DB 관련 기본 예외 클래스"""

    pass


class CollectionNotFoundError(VectorDBError):
    """컬렉션을 찾을 수 없을 때 발생하는 예외"""

    pass


class CollectionAlreadyExistsError(VectorDBError):
    """컬렉션이 이미 존재할 때 발생하는 예외"""

    pass


class EmbeddingError(VectorDBError):
    """임베딩 처리 중 발생하는 예외"""

    pass


class SearchError(VectorDBError):
    """검색 처리 중 발생하는 예외"""

    pass


class ConnectionError(VectorDBError):
    """Milvus 연결 오류"""

    pass


class DataValidationError(VectorDBError):
    """데이터 검증 오류"""

    pass


class ModelLoadError(VectorDBError):
    """모델 로드 오류"""

    pass
