"""
RAG Worker 태스크 정의
"""

import time
from typing import Dict, Any, Union, Optional
from .celery_app import app
from .git_service import GitService
from .git_service.types import CloneResult, StatusResult, PullResult, DeleteResult
from .python_parser import RepositoryParserService
from .python_parser.types import RepositoryParseResult
from .vector_db import VectorDBService
from .vector_db.types import EmbeddingResult, SearchResult
from .vector_db.config import DEFAULT_MODEL_KEY

# 서비스 인스턴스 생성
git_service = GitService()
parser_service = RepositoryParserService()
# embedding_batch_size=4: 메모리 누적 방지, 배치마다 메모리 해제
vector_db_service = VectorDBService(embedding_batch_size=4)


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


# Repository 처리 통합 작업
@app.task(name='rag_worker.tasks.process_repository_pipeline')
def process_repository_pipeline(
    repo_id: str,
    git_url: str,
    repo_name: str,
    model_key: str = DEFAULT_MODEL_KEY
) -> Dict[str, Any]:
    """
    Repository 전체 처리 파이프라인
    1. Git clone
    2. Python 파싱 및 청킹
    3. Vector DB 임베딩

    Args:
        repo_id: Repository ID (UUID)
        git_url: Git repository URL
        repo_name: Repository 이름
        model_key: 임베딩 모델 키

    Returns:
        처리 결과
    """
    import os
    import logging
    from pathlib import Path
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    logger = logging.getLogger(__name__)

    # ⚠️ IMPORTANT: backend 모듈을 import하기 전에 환경변수 설정 필수!
    env_local_path = Path(__file__).parent.parent / '.env.local'
    logger.info(f"🔍 Looking for .env.local at: {env_local_path}")
    logger.info(f"📁 .env.local exists: {env_local_path.exists()}")

    if env_local_path.exists():
        # .env.local 파일을 직접 파싱 (환경변수 우선순위 문제 방지)
        DATABASE_URL = None
        with open(env_local_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    DATABASE_URL = line.split('=', 1)[1]
                    break

        if DATABASE_URL:
            # 환경변수로 강제 설정
            os.environ['DATABASE_URL'] = DATABASE_URL
            logger.info(f"✅ Set DATABASE_URL from .env.local: {DATABASE_URL}")
        else:
            DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/ragit'
            os.environ['DATABASE_URL'] = DATABASE_URL
            logger.warning(f"⚠️ DATABASE_URL not found in .env.local, using default: {DATABASE_URL}")
    else:
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ragit')
        logger.info(f"⚠️ .env.local not found, using environment: {DATABASE_URL}")

    # 이제 backend 모듈 import (환경변수가 이미 설정됨)
    from backend.services.repository_service import RepositoryService

    # 데이터베이스 세션 생성
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    logger.info(f"🔗 Database connection created successfully")

    try:
        # 1. 상태를 'syncing'으로 업데이트
        RepositoryService.update_repository_status(db, repo_id, "syncing", "pending")

        # 2. Git Clone
        clone_result = git_service.clone_repository(git_url, repo_name)
        if not clone_result['success']:
            RepositoryService.update_repository_status(db, repo_id, "error", "error")
            return {
                "success": False,
                "error": f"Git clone failed: {clone_result['message']}",
                "step": "clone"
            }

        # 3. Python 파일 파싱 및 청킹
        parse_result = parser_service.parse_repository(repo_name, save_json=True)
        if not parse_result['success']:
            RepositoryService.update_repository_status(db, repo_id, "error", "error")
            return {
                "success": False,
                "error": f"Parsing failed: {parse_result['message']}",
                "step": "parse"
            }

        # 파일 개수 업데이트
        file_count = parse_result['total_files']
        RepositoryService.update_file_count(db, repo_id, file_count)

        # 4. Vector DB 상태를 'syncing'으로 업데이트
        RepositoryService.update_repository_status(db, repo_id, "syncing", "syncing")

        # 5. Vector DB 임베딩
        collection_name = f"repo_{repo_id.replace('-', '_')}"
        embed_result = vector_db_service.embed_repository(repo_name, collection_name, model_key)

        if not embed_result['success']:
            RepositoryService.update_repository_status(db, repo_id, "active", "error")
            return {
                "success": False,
                "error": f"Embedding failed: {embed_result['message']}",
                "step": "embed",
                "file_count": file_count
            }

        # 6. Collections count 증가
        RepositoryService.increment_collections_count(db, repo_id)

        # 7. 최종 상태를 'active'로 업데이트
        RepositoryService.update_repository_status(db, repo_id, "active", "active")

        return {
            "success": True,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "file_count": file_count,
            "total_chunks": parse_result['total_chunks'],
            "collection_name": collection_name,
            "embedded_count": embed_result['inserted_count'],
            "message": "Repository processed successfully"
        }

    except Exception as e:
        # 오류 발생 시 상태 업데이트
        RepositoryService.update_repository_status(db, repo_id, "error", "error")
        return {
            "success": False,
            "error": str(e),
            "step": "unknown"
        }
    finally:
        db.close()


# Chat RAG 작업
@app.task(name='rag_worker.tasks.chat_query')
def chat_query(
    chat_room_id: str,
    repo_id: str,
    user_message: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    사용자 메시지에 대한 RAG 기반 응답 생성

    Args:
        chat_room_id: 채팅방 ID
        repo_id: 레포지토리 ID
        user_message: 사용자 메시지
        top_k: 검색할 코드 조각 개수

    Returns:
        응답 결과
    """
    import os
    import logging
    import json
    from pathlib import Path
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    logger = logging.getLogger(__name__)

    # DATABASE_URL 설정 (process_repository_pipeline과 동일한 로직)
    env_local_path = Path(__file__).parent.parent / '.env.local'

    if env_local_path.exists():
        DATABASE_URL = None
        with open(env_local_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    DATABASE_URL = line.split('=', 1)[1]
                    break

        if DATABASE_URL:
            os.environ['DATABASE_URL'] = DATABASE_URL
            logger.info(f"✅ Set DATABASE_URL from .env.local")
        else:
            DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/ragit'
            os.environ['DATABASE_URL'] = DATABASE_URL
            logger.warning(f"⚠️ DATABASE_URL not found in .env.local, using default")
    else:
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ragit')
        logger.info(f"⚠️ .env.local not found, using environment")

    # backend 모듈 import
    from backend.services.chat_service import ChatMessageService
    from backend.schemas.chat import ChatMessageCreate

    # 데이터베이스 세션 생성
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    logger.info(f"🔗 Database connection created successfully")

    try:
        # 1. Vector DB 검색
        collection_name = f"repo_{repo_id.replace('-', '_')}"
        logger.info(f"🔍 Searching vectors in collection: {collection_name}")
        logger.info(f"📝 User query: {user_message}")

        search_result = vector_db_service.search(
            query=user_message,
            collection_name=collection_name,
            model_key=DEFAULT_MODEL_KEY,
            top_k=top_k
        )

        if not search_result['success']:
            logger.error(f"❌ Vector search failed: {search_result.get('error')}")
            # 검색 실패시에도 기본 응답 생성
            bot_response = "죄송합니다. 코드 검색 중 오류가 발생했습니다. 나중에 다시 시도해주세요."
            sources = None
        else:
            logger.info(f"✅ Found {search_result['total_results']} relevant code snippets")

            # 2. 검색 결과를 바탕으로 LLM 응답 생성 (현재는 하드코딩)
            # TODO: 나중에 실제 LLM API 호출로 교체

            retrieved_codes = search_result['results'][:top_k]

            # 하드코딩된 응답 생성
            if retrieved_codes:
                code_summary = []
                for i, code in enumerate(retrieved_codes, 1):
                    code_summary.append(f"{i}. {code['name']} ({code['file_path']}:{code['start_line']}-{code['end_line']})")

                bot_response = f"""안녕하세요! 질문해주신 내용과 관련된 코드를 찾았습니다.

**검색된 코드 조각:**
{chr(10).join(code_summary)}

**분석 결과:**
해당 레포지토리에서 관련된 코드를 {len(retrieved_codes)}개 발견했습니다. 위 코드들이 질문과 연관이 있을 것으로 보입니다.

더 구체적인 질문이 있으시면 말씀해주세요!

*참고: 현재는 코드 검색 기능만 활성화되어 있으며, 향후 LLM 기반 상세 분석이 추가될 예정입니다.*"""

                # sources를 JSON 문자열로 저장
                sources = json.dumps([
                    f"{code['file_path']}:{code['start_line']}-{code['end_line']}"
                    for code in retrieved_codes
                ], ensure_ascii=False)
            else:
                bot_response = "질문하신 내용과 관련된 코드를 찾지 못했습니다. 다른 방식으로 질문해주시겠어요?"
                sources = None

        # 3. Bot 메시지를 DB에 저장
        logger.info(f"💾 Saving bot response to database")

        bot_message_data = ChatMessageCreate(
            chat_room_id=chat_room_id,
            sender_type="bot",
            content=bot_response,
            sources=sources
        )

        bot_message = ChatMessageService.create_message(
            db=db,
            message_data=bot_message_data,
            user_id=None  # bot 메시지는 user_id가 None
        )

        logger.info(f"✅ Bot message saved with ID: {bot_message.id}")

        return {
            "success": True,
            "chat_room_id": chat_room_id,
            "bot_message_id": str(bot_message.id),
            "retrieved_count": search_result.get('total_results', 0) if search_result['success'] else 0,
            "message": "Chat query processed successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error processing chat query: {str(e)}", exc_info=True)

        # 에러 발생 시에도 에러 메시지를 bot 응답으로 저장
        try:
            error_message_data = ChatMessageCreate(
                chat_room_id=chat_room_id,
                sender_type="bot",
                content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
                sources=None
            )
            ChatMessageService.create_message(db, error_message_data, None)
        except:
            pass

        return {
            "success": False,
            "error": str(e),
            "chat_room_id": chat_room_id
        }

    finally:
        db.close()
