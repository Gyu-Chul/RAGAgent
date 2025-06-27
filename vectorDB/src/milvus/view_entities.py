from pymilvus import connections, Collection, utility

def view_entities(collection_name: str) -> str:
    try:
        connections.connect(alias="default", host="127.0.0.1", port=19530)

        if not utility.has_collection(collection_name):
            return f"❌ 컬렉션 '{collection_name}' 이(가) 존재하지 않습니다."

        collection = Collection(name=collection_name)
        collection.load()

        results = collection.query(
            expr="",  # 모든 엔티티
            output_fields=["id", "embedding", "text"],
            limit=100
        )

        if not results:
            return f"⚠️ '{collection_name}' 컬렉션에 데이터가 없습니다."

        logs = [f"✅ '{collection_name}'에서 {len(results)}개 엔티티 조회됨:\n"]
        for idx, item in enumerate(results, 1):
            log = (
                f"[{idx}] ID: {item.get('id', 'N/A')}\n"
                f"     Vector snippet: {item['embedding'][:5]} (dim: {len(item['embedding'])})\n"
                f"     Text: {item['text'][:150]}...\n"
            )
            logs.append(log)
        return "\n".join(logs)

    except Exception as e:
        return f"❌ 조회 중 오류 발생: {e}"
