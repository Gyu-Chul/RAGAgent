"""
RAG Worker 태스크 정의
"""

import time
from typing import Dict, Any, Union, Optional, List
from .celery_app import app
from .git_service import GitService
from .git_service.types import CloneResult, StatusResult, PullResult, DeleteResult
from .python_parser import RepositoryParserService
from .python_parser.types import RepositoryParseResult
from .vector_db import VectorDBService
from .vector_db.types import EmbeddingResult, SearchResult
from .vector_db.config import DEFAULT_MODEL_KEY
from .ask_question import PromptGenerator

# 서비스 인스턴스 생성
git_service = GitService()
parser_service = RepositoryParserService()
# embedding_batch_size=4: 메모리 누적 방지, 배치마다 메모리 해제
vector_db_service = VectorDBService(embedding_batch_size=4)
prompt_service = PromptGenerator()


@app.task
def process_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 처리 태스크

    Args:
        document_data: 처리할 문서 데이터

    Returns:
        처리 결과
    """
    # TODO: 실제 문서 처리 로직 구현
    return {
        "status": "processed",
        "document_id": document_data.get("id"),
        "message": "Document processed successfully"
    }


@app.task
def search_documents(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    문서 검색 태스크

    Args:
        query: 검색 쿼리
        limit: 결과 제한 수

    Returns:
        검색 결과
    """
    # TODO: 실제 검색 로직 구현
    return {
        "query": query,
        "results": [],
        "total": 0,
        "message": "Search completed"
    }


@app.task
def health_check() -> Dict[str, str]:
    """
    헬스 체크 태스크

    Returns:
        상태 정보
    """
    return {"status": "healthy", "service": "rag_worker"}


# 테스트용 기본 태스크
@app.task
def add(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
    """두 숫자를 더하는 작업"""
    result = x + y
    return result


@app.task
def reverse_string(text: str) -> str:
    """문자열을 뒤집는 작업"""
    result = text[::-1]
    return result


@app.task
def wait_seconds(second: int) -> int:
    """지정된 시간만큼 대기하는 작업"""
    time.sleep(second)
    return second


# Git 관련 작업
@app.task
def git_clone(git_url: str, repo_name: Optional[str] = None) -> CloneResult:
    """
    Git 레포지토리 클론 작업

    Args:
        git_url: Git 레포지토리 URL
        repo_name: 저장할 레포지토리 이름 (선택)

    Returns:
        클론 결과
    """
    return git_service.clone_repository(git_url, repo_name)


@app.task
def git_check_status(repo_name: str) -> StatusResult:
    """
    레포지토리 커밋 상태 확인 작업

    Args:
        repo_name: 레포지토리 이름

    Returns:
        커밋 상태 정보
    """
    return git_service.check_commit_status(repo_name)


@app.task
def git_pull(repo_name: str) -> PullResult:
    """
    레포지토리 pull 작업

    Args:
        repo_name: 레포지토리 이름

    Returns:
        Pull 결과
    """
    return git_service.pull_repository(repo_name)


@app.task
def git_delete(repo_name: str) -> DeleteResult:
    """
    레포지토리 삭제 작업

    Args:
        repo_name: 레포지토리 이름

    Returns:
        삭제 결과
    """
    return git_service.delete_repository(repo_name)


# Python 파싱 관련 작업
@app.task
def parse_repository(repo_name: str, save_json: bool = True) -> RepositoryParseResult:
    """
    레포지토리 내 모든 Python 파일을 파싱하여 청킹

    Args:
        repo_name: 레포지토리 이름
        save_json: JSON 파일로 저장 여부 (기본값: True)

    Returns:
        레포지토리 파싱 결과
    """
    return parser_service.parse_repository(repo_name, save_json)


# Vector DB 관련 작업
@app.task
def embed_documents(
    json_path: str, collection_name: str, model_key: str = DEFAULT_MODEL_KEY
) -> EmbeddingResult:
    """
    JSON 파일의 문서를 임베딩하여 Milvus 컬렉션에 저장

    Args:
        json_path: JSON 파일 경로
        collection_name: 저장할 컬렉션 이름
        model_key: 사용할 임베딩 모델 키 (기본값: DEFAULT_MODEL_KEY)

    Returns:
        임베딩 결과
    """
    return vector_db_service.embed_documents(json_path, collection_name, model_key)


@app.task
def embed_repository(
    repo_name: str, collection_name: str, model_key: str = DEFAULT_MODEL_KEY
) -> EmbeddingResult:
    """
    파싱된 레포지토리 전체를 임베딩하여 Milvus 컬렉션에 저장

    Args:
        repo_name: 레포지토리 이름 (parsed_repository/{repo_name}/ 의 모든 JSON 수집)
        collection_name: 저장할 컬렉션 이름
        model_key: 사용할 임베딩 모델 키 (기본값: DEFAULT_MODEL_KEY)

    Returns:
        임베딩 결과
    """
    return vector_db_service.embed_repository(repo_name, collection_name, model_key)


@app.task
def search_vectors(
    query: str,
    collection_name: str,
    model_key: str = DEFAULT_MODEL_KEY,
    top_k: int = 5,
    filter_expr: Optional[str] = None,
) -> SearchResult:
    """
    하이브리드 검색 수행 (밀집 + 희소 벡터)

    Args:
        query: 검색 쿼리
        collection_name: 검색할 컬렉션 이름
        model_key: 사용할 임베딩 모델 키 (기본값: DEFAULT_MODEL_KEY)
        top_k: 반환할 결과 개수 (기본값: 5)
        filter_expr: 필터 표현식 (선택)

    Returns:
        검색 결과
    """
    return vector_db_service.search(query, collection_name, model_key, top_k, filter_expr)

@app.task
def create_prompt(
    docs: List[SearchResult],
    query: str,
) -> str:
    """
    검색 결과를 이용한 프롬프트 생성

    Args:
        SearchResult: 검색 결과
        query: 검색 쿼리

    Returns:
        생성된 프롬프트
    """
    return prompt_service.create(docs, query)


