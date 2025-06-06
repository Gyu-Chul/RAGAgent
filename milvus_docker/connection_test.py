# test.py
from pymilvus import connections, utility

# 1) Milvus 서버에 연결 (기본 호스트: localhost, 포트: 19530)
connections.connect(alias="default", host="127.0.0.1", port=19530)

# 2) 연결 상태 확인 (ping() 대신 list_collections() 사용)
try:
    cols = utility.list_collections()
    print("✅ Milvus 연결 성공! 현재 컬렉션 목록:", cols)
except Exception as e:
    print("❌ Milvus 연결 또는 호출 실패:", e)
