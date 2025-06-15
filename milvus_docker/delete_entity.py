from pymilvus import connections, Collection

def delete_entity():
    connections.connect(alias="default", host="127.0.0.1", port=19530)

    collection_name = input("🗑 삭제할 대상 컬렉션 이름: ").strip()
    collection = Collection(name=collection_name)

    results = collection.query(
        expr="", 
        output_fields=["id", "text"], 
        limit=10
    )
    for item in results:
        print("ID:", item["id"], "\n", item["text"][:100], "\n")

    collection.load()

    entity_id = input("🔍 삭제할 엔티티의 ID를 입력하세요: ").strip()
    if not entity_id.isdigit():
        print("❌ 숫자 ID만 입력하세요.")
        return

    expr = f"id in [{entity_id}]"
    collection.delete(expr=expr)
    collection.flush()

    print(f"✅ ID {entity_id} 삭제 완료")

if __name__ == "__main__":
    delete_entity()
