from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection

def create_collection() :
    # Milvus에 “default”라는 alias 이름으로 연결
    connections.connect(
        alias="default",
        host="127.0.0.1",
        port=19530
    )

    collection_name = input("Name of Collection: ")
    description = input("Description about Collection: ")

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
    text_field = FieldSchema(
    name="text",
    dtype=DataType.VARCHAR,
    max_length=65535,
    )
    schema = CollectionSchema(
        fields=[id_field, vector_field, text_field],
        description=description
    )



    ####### 컬렉션 생성
    if not utility.has_collection(collection_name):
        collection = Collection(name=collection_name, schema=schema)
        print(f"컬렉션 '{collection_name}' 생성 완료")
                # 인덱스 자동 생성 추가
        index_params = {
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
            "metric_type": "L2"
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print("🔧 인덱스 생성 완료")
    else:
        collection = Collection(name=collection_name)
        print(f"컬렉션 '{collection_name}' 이미 존재, Load 완료")



if __name__ == "__main__":
    create_collection()
