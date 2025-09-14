from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema
import config

# Milvus 클라이언트를 한 번만 생성하여 재사용
try:
    client = MilvusClient(uri=config.MILVUS_URI)
    print("✅ Milvus 유틸리티 초기화 완료. 서버에 연결되었습니다.")
except Exception as e:
    print(f"❌ Milvus 유틸리티 초기화 실패: {e}")
    client = None

def create_milvus_collection(collection_name: str, dim: int = 768):
    """지정된 이름과 차원으로 Milvus 컬렉션을 생성합니다."""
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return
        
    if client.has_collection(collection_name):
        print(f"⚠️ 컬렉션 '{collection_name}'은(는) 이미 존재합니다.")
    else:
        # 👇 LangChain이 기대하는 스키마를 직접 정의합니다.
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        schema = CollectionSchema(fields=fields, description="LangChain compatible collection")
        
        # 정의된 스키마로 컬렉션 생성
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            primary_field_name="pk",      # LangChain 기본값
            vector_field_name="vector",   # LangChain 기본값
            id_type="int"                 # LangChain 기본값
        )
        print(f"✅ LangChain 호환 컬렉션 '{collection_name}' (dim={dim})을(를) 생성했습니다.")

def list_milvus_collections():
    """모든 Milvus 컬렉션 목록을 출력합니다."""
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return
        
    collections = client.list_collections()
    if not collections:
        print("ℹ️ 현재 생성된 컬렉션이 없습니다.")
    else:
        print("📚 존재하는 컬렉션 목록:")
        for name in collections:
            stats = client.get_collection_stats(name)
            print(f"- {name} (Entities: {stats.get('row_count', 0)})")

def delete_milvus_collection(collection_name: str):
    """지정된 이름의 Milvus 컬렉션을 삭제합니다."""
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return
        
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)
        print(f"🗑️ 컬렉션 '{collection_name}'을(를) 삭제했습니다.")
    else:
        print(f"⚠️ 컬렉션 '{collection_name}'을(를) 찾을 수 없습니다.")