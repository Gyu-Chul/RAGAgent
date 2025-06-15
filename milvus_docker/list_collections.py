from pymilvus import utility, connections
from pymilvus.exceptions import MilvusException

def list_collections():
    try:
        connections.connect(
            alias="default",
            host="127.0.0.1",
            port=19530
        )
    except Exception as e:
        print(f"❌ Milvus 연결 실패: {e}")
        return

    try:
        collections = utility.list_collections()
    except MilvusException as e:
        print(f"❌ 컬렉션 조회 중 오류 발생: {e}")
        return

    if not collections:
        print("⚠️ 현재 존재하는 컬렉션이 없습니다.")
    else:
        print("✅ 현재 존재하는 컬렉션 목록:")
        for name in collections:
            print("-", name)

if __name__ == "__main__":
    list_collections()
