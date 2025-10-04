"""
RAG Worker Git Service 테스트 클라이언트

사용법:
1. Redis와 RAG Worker가 실행 중이어야 합니다
2. python test_git_worker.py 실행
"""

import time
from typing import Any, Dict
from celery import Celery
from celery.result import AsyncResult


# Celery 앱 설정 (로컬 환경)
app = Celery(
    'test_client',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)


def print_result(task_name: str, result: Any) -> None:
    """결과를 예쁘게 출력"""
    print(f"\n{'='*60}")
    print(f"📋 Task: {task_name}")
    print(f"{'='*60}")

    if isinstance(result, dict):
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {result}")

    print(f"{'='*60}\n")


def wait_for_result(async_result: AsyncResult, timeout: int = 30) -> Any:
    """태스크 결과를 기다림"""
    print(f"⏳ 작업 대기 중... (Task ID: {async_result.id})")

    try:
        result = async_result.get(timeout=timeout)
        print(f"✅ 작업 완료!")
        return result
    except Exception as e:
        print(f"❌ 작업 실패: {str(e)}")
        return {"success": False, "error": str(e)}


def test_git_clone() -> None:
    """Git Clone 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 1: Git Clone")
    print("🔷" * 30)

    # 테스트용 공개 레포지토리 (Python 프로젝트)
    git_url = "https://github.com/psf/requests.git"
    repo_name = "requests-test"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.git_clone',
        args=[git_url],
        kwargs={'repo_name': repo_name}
    )

    # 결과 대기
    result = wait_for_result(task, timeout=60)
    print_result("git_clone", result)


def test_git_check_status() -> None:
    """Git Status 확인 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 2: Git Check Status")
    print("🔷" * 30)

    repo_name = "requests-test"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.git_check_status',
        args=[repo_name]
    )

    # 결과 대기
    result = wait_for_result(task)
    print_result("git_check_status", result)


def test_git_pull() -> None:
    """Git Pull 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 3: Git Pull")
    print("🔷" * 30)

    repo_name = "requests-test"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.git_pull',
        args=[repo_name]
    )

    # 결과 대기
    result = wait_for_result(task)
    print_result("git_pull", result)


def test_parse_repository() -> None:
    """Repository Parse 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 4: Parse Repository")
    print("🔷" * 30)

    repo_name = "requests-test"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.parse_repository',
        args=[repo_name],
        kwargs={'save_json': True}
    )

    # 결과 대기
    result = wait_for_result(task, timeout=120)
    print_result("parse_repository", result)


def test_embed_repository() -> None:
    """Repository Embedding 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 5: Embed Repository")
    print("🔷" * 30)

    repo_name = "requests-test"
    collection_name = "requests_collection"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.embed_repository',
        args=[repo_name, collection_name]
    )

    # 결과 대기
    result = wait_for_result(task, timeout=600)  # 10분 타임아웃
    print_result("embed_repository", result)


def test_search_vectors() -> None:
    """Vector Search 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 6: Search Vectors")
    print("🔷" * 30)

    collection_name = "requests_collection"
    query = "How to make HTTP GET request?"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.search_vectors',
        args=[query, collection_name],
        kwargs={'top_k': 3}
    )

    # 결과 대기
    result = wait_for_result(task, timeout=60)
    print_result("search_vectors", result)


def test_git_delete() -> None:
    """Git Delete 테스트"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 7: Git Delete")
    print("🔷" * 30)

    repo_name = "requests-test"

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.git_delete',
        args=[repo_name]
    )

    # 결과 대기
    result = wait_for_result(task)
    print_result("git_delete", result)


def test_existing_tasks() -> None:
    """기존 태스크 테스트 (워커 연결 확인용)"""
    print("\n" + "🔷" * 30)
    print("🧪 TEST 0: Worker Connection Check")
    print("🔷" * 30)

    # 간단한 add 태스크로 연결 확인
    task = app.send_task(
        'rag_worker.tasks.add',
        args=[10, 20]
    )

    result = wait_for_result(task, timeout=10)
    print_result("add(10, 20)", result)

    if result == 30:
        print("✅ Worker 연결 정상!")
    else:
        print("❌ Worker 연결 문제 발생")


def main() -> None:
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🚀 RAG Worker Git Service 테스트 시작")
    print("=" * 60)

    try:
        # 0. Worker 연결 확인
        test_existing_tasks()

        print("\n⏸️  3초 후 Git 테스트 시작...")
        time.sleep(3)

        # 1. Git Clone 테스트
        test_git_clone()

        time.sleep(2)

        # 2. Git Status 확인
        test_git_check_status()

        time.sleep(2)

        # 3. Git Pull 테스트
        test_git_pull()

        time.sleep(2)

        # 4. Repository Parse 테스트
        test_parse_repository()

        time.sleep(2)

        # 5. Repository Embedding 테스트
        test_embed_repository()

        time.sleep(2)

        # 6. Vector Search 테스트
        test_search_vectors()

        time.sleep(2)

        # 7. Git Delete 테스트 (마지막에)
        test_git_delete()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 에러 발생: {str(e)}")


if __name__ == "__main__":
    main()
