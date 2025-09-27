from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema
import config

try:
    client = MilvusClient(uri=config.MILVUS_URI)
    print("✅ Milvus 유틸리티 초기화 완료. 서버에 연결되었습니다.")
except Exception as e:
    print(f"❌ Milvus 유틸리티 초기화 실패: {e}")
    client = None

def create_milvus_collection(collection_name: str, dim: int):
    """하이브리드 검색을 위한 Milvus 컬렉션을 생성합니다."""
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return
        
    if client.has_collection(collection_name):
        print(f"⚠️ 컬렉션 '{collection_name}'은(는) 이미 존재합니다.")
    else:
        # 1. 하이브리드 검색을 위한 스키마 정의
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        ]
        schema = CollectionSchema(fields=fields, description="Hybrid search collection")
        
        # 2. 👇 각 벡터 필드에 대한 인덱스 파라미터 준비
        index_params = client.prepare_index_params()
        
        # 밀집 벡터용 HNSW 인덱스
        index_params.add_index(
            field_name="dense_vector",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 64},
        )
        # 희소 벡터용 SPARSE_WAND 인덱스
        index_params.add_index(
            field_name="sparse_vector",
            index_type="SPARSE_WAND",
            metric_type="IP",
            params={"drop_ratio_build": 0.2},
        )
        
        print(f"하이브리드 스키마로 '{collection_name}' 컬렉션 생성 중...")

        # 3. 👇 스키마와 인덱스 파라미터를 함께 전달하여 컬렉션 생성
        client._create_collection_with_schema(
            collection_name=collection_name, 
            schema=schema, 
            index_params=index_params
        )
        
        print(f"✅ 하이브리드 컬렉션 '{collection_name}' 생성 완료.")


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