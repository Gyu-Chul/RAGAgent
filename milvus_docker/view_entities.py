from pymilvus import connections, Collection, utility

def view_entities():
    connections.connect(alias="default", host="127.0.0.1", port=19530)

    collections = utility.list_collections()
    print("✅ 현재 존재하는 컬렉션 목록:")
    for name in collections:
        print("-", name)

    collection_name = input("🔍 내용을 조회할 Milvus 컬렉션 이름을 입력하세요: ").strip()
    collection = Collection(name=collection_name)
    collection.load()

    try:
        results = collection.query(
            expr="",
            output_fields=["id", "embedding", "text"],
            limit=100
        )
    except Exception as e:
        print(f"❌ 쿼리 중 오류 발생: {e}")
        return

    if not results:
        print("⚠️ 컬렉션에 데이터가 없습니다.")
    else:
        print(f"\n✅ '{collection_name}' 컬렉션에서 가져온 엔티티:")
        for idx, item in enumerate(results, 1):
            print(f"[{idx}] ID: {item.get('id', 'N/A')}")
            print("     Vector snippet:", item["embedding"][:5], "...")
            print(f"     Full dim: {len(item['embedding'])}\n")
            print(f"     Code (text field):\n{item['text'][:300]}...\n")

if __name__ == "__main__":
    view_entities()
