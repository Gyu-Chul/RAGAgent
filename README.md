
# RAG AGENT 내부 테스트 실행 가이드



1. Redis 실행 : `docker run --name my-redis -p 6379:6379 -d redis`
2. Celery 프로세스 실행 : `celery -A main worker --loglevel=info -P solo`
   - rag_worker 디렉토리 안에서 명령어 실행할 것
   - celery 라이브러리는 Linux,Unix 기반으로 개발되어 윈도우에서는 제약이 발생함.
   - solo 모드로 실행하거나, 추후 eventlet 기능을 통한 확장 필요






## 기타 명령어 

모듈 의존성 파일 저장하기 : `pip freeze > requirements.txt`