#main.py

import time
from celery import Celery

app = Celery('tasks',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

@app.task
def add(x, y):
    result = x + y
    return result

@app.task
def reverse_string(text):
    result = text[::-1]
    return result

@app.task
def wait_seconds(second:int):
    time.sleep(second)
    return second