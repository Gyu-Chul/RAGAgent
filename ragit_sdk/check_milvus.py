"""
Milvus 데이터 확인 스크립트

사용법: python -m ragit_sdk.check_milvus
"""

from pymilvus import MilvusClient, Collection, connections

MILVUS_URI = "http://localhost:19530"


def check_collections() -> None:
    """모든 컬렉션 확인"""
    print("\n" + "="*60)
    print("📊 Milvus Collections")
    print("="*60)

    try:
        # MilvusClient 연결
        client = MilvusClient(uri=MILVUS_URI)

        # 컬렉션 목록
        collections = client.list_collections()

        if not collections:
            print("\n❌ No collections found!")
            return

        print(f"\n✅ Found {len(collections)} collection(s):\n")

        # PyMilvus 연결
        connections.connect(alias="default", uri=MILVUS_URI)

        for name in collections:
            print(f"📁 Collection: {name}")

            try:
                collection = Collection(name)
                collection.load()

                # 엔티티 수 조회
                count_result = collection.query(
                    expr="pk > 0",
                    output_fields=["count(*)"]
                )
                count = count_result[0]["count(*)"] if count_result else 0

                print(f"   📊 Total entities: {count}")

                # 샘플 데이터 조회 (처음 3개)
                if count > 0:
                    samples = collection.query(
                        expr="pk > 0",
                        output_fields=["pk", "text", "file_path", "type", "name", "_source_file"],
                        limit=3
                    )

                    print(f"   📄 Sample data:")
                    for i, sample in enumerate(samples, 1):
                        print(f"\n      Sample {i}:")
                        print(f"      - PK: {sample.get('pk')}")
                        print(f"      - Type: {sample.get('type')}")
                        print(f"      - Name: {sample.get('name')}")
                        print(f"      - Source File: {sample.get('_source_file')}")
                        print(f"      - File Path: {sample.get('file_path', '')[:80]}...")
                        print(f"      - Code Preview: {sample.get('text', '')[:100]}...")

            except Exception as e:
                print(f"   ❌ Error: {e}")

            print("\n" + "-"*60 + "\n")

    except Exception as e:
        print(f"\n❌ Failed to connect to Milvus: {e}")


if __name__ == "__main__":
    check_collections()
