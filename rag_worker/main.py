"""
RAG Worker - Celery 백그라운드 작업 처리
"""

import time
from celery import Celery
from typing import Union

app = Celery('tasks',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')


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