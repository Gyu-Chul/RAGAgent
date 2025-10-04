"""
RAG Worker 검색 기능만 테스트

사용법:
1. Redis 서버 실행 확인
2. Celery Worker 실행 확인
3. python -m ragit_sdk.tests.test_search_only 실행 또는 ragit test search
"""

from celery import Celery
from celery.result import AsyncResult


# Celery 앱 설정
app = Celery(
    'test_search',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)


def test_search_vectors() -> None:
    """Vector Search 테스트"""
    print("\n" + "="*60)
    print("🔍 Vector Search Test")
    print("="*60)

    collection_name = "tablib_collection"
    query = "How to export data to JSON?"

    print(f"\n📌 Collection: {collection_name}")
    print(f"📌 Query: {query}")
    print(f"\n⏳ Sending task to Celery worker...")

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.search_vectors',
        args=[query, collection_name],
        kwargs={'top_k': 3}
    )

    print(f"✅ Task sent! (Task ID: {task.id})")
    print(f"⏳ Waiting for result...\n")

    # 결과 대기
    try:
        result = task.get(timeout=60)

        print("="*60)
        print("📋 Search Result")
        print("="*60)

        print(f"\nSuccess: {result.get('success')}")
        print(f"Query: {result.get('query')}")
        print(f"Collection: {result.get('collection_name')}")
        print(f"Total Results: {result.get('total_results')}")
        print(f"Elapsed Time: {result.get('elapsed_time'):.2f}s")

        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")

        if result.get('results'):
            print(f"\n📄 Search Results:")
            for i, item in enumerate(result['results'], 1):
                print(f"\n--- Result {i} ---")
                print(f"Score: {item.get('score', 'N/A')}")
                print(f"Type: {item.get('type')}")
                print(f"Name: {item.get('name')}")
                print(f"File: {item.get('_source_file')}")
                print(f"Lines: {item.get('start_line')}-{item.get('end_line')}")
                print(f"Code Preview:\n{item.get('code', '')[:200]}...")

        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ Task failed: {str(e)}")


if __name__ == "__main__":
    test_search_vectors()
