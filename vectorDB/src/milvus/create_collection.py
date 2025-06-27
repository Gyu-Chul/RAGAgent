from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection

def create_collection(collection_name: str, description: str = "") -> str:
    try:
        connections.connect(alias="default", host="127.0.0.1", port=19530)

        id_field = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        vector_field = FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=768
        )
        text_field = FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=65535
        )
        schema = CollectionSchema(
            fields=[id_field, vector_field, text_field],
            description=description
        )

        if not utility.has_collection(collection_name):
            collection = Collection(name=collection_name, schema=schema)
            index_params = {
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
                "metric_type": "L2"
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            return f"✅ 컬렉션 '{collection_name}' 생성 및 인덱스 구성 완료"
        else:
            return f"⚠️ 컬렉션 '{collection_name}' 이미 존재함 (건너뜀)"
    except Exception as e:
        return f"❌ 컬렉션 생성 실패: {e}"
