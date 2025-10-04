"""
RAG Worker 검색 기능만 테스트

사용법:
1. Redis 서버 실행 확인
2. Celery Worker 실행 확인
3. python -m ragit_sdk.tests.test_search_only 실행 또는 ragit test search
"""

from celery import Celery
from celery.result import AsyncResult
from typing import List, Optional, TypedDict

# Celery 앱 설정
app = Celery(
    'test_search',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)


def ask_question() -> None:
    """llm api 전송 테스트"""
    print("\n" + "="*60)
    print("LLM Ask Test")
    print("="*60)

    prompt = "This is prompt"
    use_stream = True
    query = "How to export data to JSON?"

    print(f"📌 Query: {query}")
    print(f"\n⏳ Sending task to Celery worker...")

    # Task 전송
    task = app.send_task(
        'rag_worker.tasks.call_llm',
        kwargs={
            'prompt': prompt,
            'use_stream': use_stream,
        }
    )

    print(f"✅ Task sent! (Task ID: {task.id})")
    print(f"⏳ Waiting for result...\n")

    # 결과 대기
    try:
        result = task.get(timeout=60)

        print("="*60)
        print("📋 Search Result")
        print("="*60)

        print(result)


        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ Task failed: {str(e)}")


if __name__ == "__main__":
    ask_question()
