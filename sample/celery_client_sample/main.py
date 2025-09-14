# celery_client_sample/main.py

from celery import Celery
import time
import redis  # redis 라이브러리 import
import json  # json 라이브러리 import


def inspect_redis_status(message):
    """현재 Redis의 Celery 관련 데이터를 출력하는 함수"""
    print(f"\n========== [Redis 상태 확인: {message}] ==========")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()

        queue_name = 'celery'
        queue_length = r.llen(queue_name)
        print(f"[*] 대기열('{queue_name}')의 작업 수: {queue_length}개")

        result_keys = r.keys('celery-task-meta-*')
        print(f"[*] 저장된 결과 수: {len(result_keys)}개")

    except redis.exceptions.ConnectionError as e:
        print(f"❌ Redis 연결 실패: {e}")
    finally:
        print("====================================================\n")

client_app = Celery(
    'celery_client',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

TASK_ADD = 'main.add'
TASK_REVERSE = 'main.reverse_string'
TASK_TIME = 'main.wait_seconds'

if __name__ == '__main__':
    result3 = client_app.send_task(TASK_TIME, args=[1])
    result4 = client_app.send_task(TASK_TIME, args=[1])
    result5 = client_app.send_task(TASK_TIME, args=[1])
    result6 = client_app.send_task(TASK_TIME, args=[1])
    inspect_redis_status("1초 시간 task 4개 생성후")

    print("원격 태스크를 브로커에게 전송합니다.")

    result1 = client_app.send_task(TASK_ADD, args=[100, 200])
    result2 = client_app.send_task(TASK_REVERSE, kwargs={'text': "Remote Hello!"})

    print(f"태스크가 전송되었습니다. Task ID: {result1.id}")
    print(f"태스크가 전송되었습니다. Task ID: {result2.id}")
    print("\n클라이언트는 다른 작업을 계속 수행할 수 있습니다...")

    inspect_redis_status("작업 전송 직후")


    inspect_redis_status("결과 확인 직전")

    print(f"\n작업 ID {result1.id}의 결과를 기다리는 중...")

    final_result = result1.get()


    print(f"결과 수신: {final_result}")
    task_meta1 = result1.backend.get_task_meta(result1.id)

    print("--- Redis에 저장된 Task 1의 전체 정보 ---")
    print(json.dumps(task_meta1, indent=2, ensure_ascii=False))
    print("-" * 40)


    inspect_redis_status("모든 작업 완료 후")