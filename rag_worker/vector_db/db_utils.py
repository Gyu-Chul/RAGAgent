from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema, utility, Collection, connections
import config


######## 최초로 Milvus에 접속하는 시작점
######## from db_utils import client 를 통해 다른 위치에서도 한 번 접속한 것으로 활용
try:
    client = MilvusClient(uri=config.MILVUS_URI)
    print("✅ Milvus 유틸리티 초기화 완료. 서버에 연결되었습니다.")
except Exception as e:
    print(f"❌ Milvus 유틸리티 초기화 실패: {e}")
    client = None

def create_milvus_collection(collection_name: str, dim: int):
    """MilvusClient를 사용하여 컬렉션과 인덱스를 생성합니다."""
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return
        
    if client.has_collection(collection_name):
        print(f"⚠️ 컬렉션 '{collection_name}'은(는) 이미 존재합니다.")
        return

    analyzer_params = {
        "type": "english"
    }
    # --- 1. 스키마 정의 ---
    fields = [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65_535),
        FieldSchema(name="dense", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="start_line", dtype=DataType.INT64),
        FieldSchema(name="end_line", dtype=DataType.INT64),
        FieldSchema(name="type", 
                    dtype=DataType.VARCHAR, 
                    max_length=256,
                    enable_analyzer=True,
                    analyzer_params = analyzer_params,
                    enable_match = True,
                    ),
        FieldSchema(name="_source_file", 
                    dtype=DataType.VARCHAR, 
                    max_length=1024,
                    enable_analyzer=True, # Whether to enable text analysis for this field
                    enable_match=True, # Whether to enable text match
                    analyzer_params = {"type": "english"}
                    ),
    ]
    schema = CollectionSchema(fields=fields, 
                              description="Optimized hybrid search collection",
                              enable_dynamic_field=True  # 동적 필드 활성화 - dense, sparse를 직접 스키마-인데스 연결해주지 않아도 알아서 처리
                              )
    
    # --- 2. 스키마로 컬렉션 생성 ---
    print(f"스키마로 '{collection_name}' 컬렉션 생성 중...")
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        consistency_level="Strong" # 데이터 일관성을 유지
    )
    print(f"✅ 컬렉션 생성 완료. 이제 인덱스를 생성합니다...")

    # --- 3. 인덱스 파라미터 빌더 준비 및 모든 인덱스 정보 추가 ---
    print("인덱스 파라미터 준비 중...")
    # 3-1. 빌더 객체 생성
    index_params = client.prepare_index_params()

    # 3-2. 빌더에 dense 필드의 인덱스 정보를 추가
    index_params.add_index(
        field_name="dense",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 256}
    )

    # 3-3. 빌더에 sparse 필드의 인덱스 정보를 추가
    index_params.add_index(
        field_name="sparse",
        index_type="SPARSE_WAND",
        metric_type="IP",
        params={"drop_ratio_build": 0.2}
    )

    # 3-4. 빌더에 스칼라 필드의 인덱스 정보를 추가 (MetaData활용)
    index_params.add_index(field_name="file_path")
    index_params.add_index(field_name="type")
    index_params.add_index(field_name="name")
    index_params.add_index(field_name="start_line")
    index_params.add_index(field_name="end_line")
    index_params.add_index(field_name="_source_file")

    # --- 4. 빌더 객체로 모든 인덱스를 한 번에 생성 ---
    print("모든 필드에 대한 인덱스 동시 생성 중...")
    client.create_index(
        collection_name=collection_name,
        index_params=index_params
    )

    # info = client.describe_collection(collection_name=collection_name)
    # print(info)

    # print("="*50)
    # print("="*50)
    # # 컬렉션에 생성된 모든 인덱스의 '이름'을 리스트로 가져옵니다.
    # index_list = client.list_indexes(collection_name=collection_name)

    # print(f"'{collection_name}' 컬렉션에 생성된 인덱스 목록:")
    # for index_name in index_list:
    #     print(f"- {index_name}")
    # print("="*50)
    # print("="*50)

    print(f"✅ 모든 인덱스 생성 완료. '{collection_name}' 컬렉션이 준비되었습니다.")

def list_milvus_collections():
    """
    실시간 엔티티 수를 정확히 측정하기 위해 query를 통해 리스트 출력합니다.
    """
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return

    try:
        connections.connect(alias="default", uri=config.MILVUS_URI)
    except Exception as e:
        if "alias default already exists" not in str(e):
            print(f"❌ 기본 연결 설정 실패: {e}")
            return
        
    collection_names = client.list_collections()
    if not collection_names:
        print("ℹ️ 현재 생성된 컬렉션이 없습니다.")
    else:
        print("📚 존재하는 컬렉션 목록:")
        for name in collection_names:
            try:
                collection = Collection(name)
                collection.load()
                                
                # 1. 모든 엔티티 출력하기 위한 표현식 (pk가 0보다 크면 모두 해당)
                expr = "pk > 0"
                
                # 2. count(*) 쿼리를 실행하여 결과 받기
                count_result = collection.query(expr=expr, output_fields=["count(*)"])
                
                # 3. 결과 딕셔너리에서 count 값 추출
                count = count_result[0]["count(*)"]
                
                print(f"- {name} (Entities: {count})")

            except Exception as e:
                print(f"- {name} (오류 발생: {e})")

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


######## 임베딩 성공 여부를 확인하기 위한 임시 함수
def verify_collection_data(collection_name: str, limit: int = 5):
    """
    지정된 컬렉션에서 실제 데이터를 몇 개 조회하여 데이터 삽입 여부를 검증합니다.
    """
    if not client:
        print("❌ Milvus 클라이언트가 연결되지 않았습니다.")
        return

    if not client.has_collection(collection_name):
        print(f"⚠️ 컬렉션 '{collection_name}'을(를) 찾을 수 없습니다.")
        return

    try:
        connections.connect(alias="default", uri=config.MILVUS_URI)
        
        collection = Collection(collection_name)
        collection.load()
        
        results = collection.query(
            expr="pk > 0",                  # 기본 출력식
            output_fields=["*"],            # 출력하고 싶은 field 설정
            limit=limit                     # limit parameter를 활용해서 출력 개수 설정
        )
        
        print(f"\n--- 컬렉션 '{collection_name}' 데이터 샘플 (최대 {limit}개) ---")
        if not results:
            print("ℹ️ 데이터가 없습니다.")
        else:
            for i, item in enumerate(results):
                print(f"\n  [ Entity #{i+1} ]")
                # item 딕셔너리의 모든 키와 값을 순회하며 출력
                for key, value in item.items():
                    # 텍스트 필드는 너무 길 경우 일부만 표시
                    if key == 'text' and isinstance(value, str):
                        value_display = f"\"{value[:100].replace(chr(10), ' ')}...\""
                    else:
                        value_display = value
                    print(f"    - {key}: {value_display}")
        print("-------------------------------------------------")

    except Exception as e:
        print(f"❌ 데이터 검증 중 오류 발생: {e}")