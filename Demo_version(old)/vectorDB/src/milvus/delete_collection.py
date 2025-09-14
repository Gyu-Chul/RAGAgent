from pymilvus import utility, connections

def delete_collection(collection_name: str) -> str:
    try:
        connections.connect(alias="default", host="127.0.0.1", port=19530)

        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            return f"🗑️ 컬렉션 '{collection_name}' 삭제 완료"
        else:
            return f"❌ 컬렉션 '{collection_name}' 존재하지 않음"
    except Exception as e:
        return f"❌ 오류 발생: {e}"
