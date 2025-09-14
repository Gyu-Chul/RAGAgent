from pymilvus import utility, connections, FieldSchema, CollectionSchema, DataType, Collection, Index
import random


# Milvus에 “default”라는 alias 이름으로 연결
connections.connect(
    alias="default",
    host="127.0.0.1",
    port=19530
)

####### 컬렉션 스키마 정의
id_field = FieldSchema(
    name="id",
    dtype=DataType.INT64,
    is_primary=True,
    auto_id=True   # Milvus가 ID를 자동으로 생성
)
vector_field = FieldSchema(
    name="embedding",
    dtype=DataType.FLOAT_VECTOR,
    dim=768         # 벡터 차원 (모델에 맞춰서 변경)
)
schema = CollectionSchema(
    fields=[id_field, vector_field],
    description="Text embeddings collection"
)


collection_name = "text_embeddings"


####### 컬렉션 생성
if not utility.has_collection(collection_name):
    collection = Collection(name=collection_name, schema=schema)
    print(f"컬렉션 '{collection_name}' 생성 완료")
else:
    collection = Collection(name=collection_name)
    print(f"컬렉션 '{collection_name}' 이미 존재, Load 완료")



####### 더미 벡터 데이터 생성 (예시: 5개 × 768차원)
dummy_embeddings = [
    [random.random() for _ in range(768)]
    for _ in range(5)
]
insert_data = [
    #[],              # id 리스트: auto_id=True 이므로 빈 리스트
    dummy_embeddings  # 5 × 768 크기의 벡터 리스트
]




####### 데이터 삽입
insert_result = collection.insert(insert_data)

####### 삽입된 데이터를 플러시해서 영속화
collection.flush()


print("데이터 삽입 후 엔티티 수:", collection.num_entities)



####### 인덱스 생성
index_params = {
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128},
    "metric_type": "L2"
}


####### 'embedding' 필드에 대해 인덱스 생성
collection.create_index(
    field_name="embedding",
    index_params=index_params
)



####### 컬렉션 로드 (메모리로 로드)
collection.load()


####### 벡터 검색
# 예시: 삽입했던 dummy_embeddings[0]을 쿼리 벡터로 사용
query_embedding = [dummy_embeddings[0]]

search_params = {
    "metric_type": "L2",
    "params": {"nprobe": 10}
}

# 결과: top 3개 이웃 벡터를 검색
results = collection.search(
    data=query_embedding,
    anns_field="embedding",
    param=search_params,
    limit=3,
    expr=None  # Boolean 필터가 없으므로 None
)

# 결과 출력
for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Distance: {hit.distance}")
