import time

def dummy():
    print(" 5초 뒤 실행됩니다.")
    time.sleep(5)

    print("task 처리 완료.")
    return "SUCCESS"