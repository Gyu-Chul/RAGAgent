from pymilvus import connections, utility

def connection_test() -> str:
    try:
        connections.connect(alias="default", host="127.0.0.1", port=19530)
        collections = utility.list_collections()
        return f"✅ Milvus 연결 성공! 현재 컬렉션 목록: {collections}"
    except Exception as e:
        return f"❌ Milvus 연결 실패: {e}"
