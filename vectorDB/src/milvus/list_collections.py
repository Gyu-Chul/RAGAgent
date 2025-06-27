from pymilvus import utility, connections
from pymilvus.exceptions import MilvusException

def list_collections() -> list[str] | str:
    try:
        connections.connect(
            alias="default",
            host="127.0.0.1",
            port=19530
        )
    except Exception as e:
        return f"❌ Milvus 연결 실패: {e}"

    try:
        collections = utility.list_collections()
    except MilvusException as e:
        return f"❌ 컬렉션 조회 중 오류 발생: {e}"

    if not collections:
        return "⚠️ 현재 존재하는 컬렉션이 없습니다."
    return collections
