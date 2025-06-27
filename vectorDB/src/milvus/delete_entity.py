from pymilvus import connections, Collection

def delete_entity(collection_name: str, entity_id: str) -> str:
    try:
        connections.connect(alias="default", host="127.0.0.1", port=19530)
        collection = Collection(name=collection_name)
        collection.load()

        if not entity_id.isdigit():
            return "❌ 삭제 실패: 숫자 ID만 입력 가능합니다."

        expr = f"id in [{entity_id}]"
        collection.delete(expr=expr)
        collection.flush()

        return f"✅ 엔티티 ID {entity_id} 삭제 완료"
    except Exception as e:
        return f"❌ 삭제 중 오류 발생: {e}"
