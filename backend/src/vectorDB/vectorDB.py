from fastapi import APIRouter, Query
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
from pydantic import BaseModel

router = APIRouter()

###################### Connection Test
# MilvusClient 인스턴스 전역 생성 (재사용)
client = MilvusClient(uri="http://127.0.0.1:19530", token="root:Milvus")

@router.get("/connection_test")
async def connection_test():
    try:
        # ✅ list_collections() 호출로 연결 확인
        collections = client.list_collections()

        return {
            "success": True,
            "message": "✅ Milvus 연결 성공! (MilvusClient 사용)",
            "collections": collections
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Milvus 연결 실패: {e}"
        }

###################### Count Entities
@router.get("/count_entities")
async def count_entities(collection_name: str = Query(..., description="Milvus 컬렉션 이름")):
    try:
        # 컬렉션 존재 여부 확인
        if not client.has_collection(collection_name):
            return {
                "success": False,
                "collection": collection_name,
                "message": f"❌ 컬렉션 '{collection_name}' 이(가) 존재하지 않습니다."
            }

        # 컬렉션 통계 조회
        stats = client.get_collection_stats(collection_name)
        count = int(stats.get("row_count", 0))

        return {
            "success": True,
            "collection": collection_name,
            "entity_count": count,
            "message": f'📊 Collection "{collection_name}" has {count} entities.'
        }

    except Exception as e:
        return {
            "success": False,
            "collection": collection_name,
            "error_type": "UnknownError",
            "message": f'❌ 엔티티 개수 조회 실패: {e}'
        }


###################### Create Collection
class CreateCollectionRequest(BaseModel):
    collection_name: str
    description: str = ""
    version: int = 1   # ✅ 기본값 ver1

@router.post("/create_collection")
async def create_collection_api(req: CreateCollectionRequest):
    try:
        if req.version == 0:
            result = create_collection_ver0(req.collection_name, req.description)
        elif req.version == 1:
            result = create_collection_ver1(req.collection_name, req.description)
        elif req.version == 2:
            result = create_collection_ver2(req.collection_name, req.description)
        elif req.version == 3:
            result = create_collection_ver3(req.collection_name, req.description)
        else:
            return {"success": False, "message": f"❌ 지원하지 않는 버전: {req.version}"}

        return {"success": True, "message": result}

    except Exception as e:
        return {"success": False, "message": f"❌ 컬렉션 생성 중 오류: {e}"}
    

def build_schema(fields, description=""):
    return {
        "fields": fields,
        "description": description
    }

# 공통 인덱스 생성 함수
def create_index(collection_name: str, index_type: str, params: dict):
    client.create_index(
        collection_name=collection_name,
        field_name="embedding",
        index_params={
            "index_type": index_type,
            "metric_type": "L2",
            "params": params
        }
    )

# ───────────────────────────────────────────────────────
# ✅ ver0: IVF_FLAT + 다양한 메타데이터 필드
def create_collection_ver0(collection_name: str, description: str = "") -> str:
    try:
        if client.has_collection(collection_name):
            return f"⚠️ 컬렉션 '{collection_name}' 이미 존재함"

        # ✅ 필드 정의
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="start_line", dtype=DataType.INT64),
            FieldSchema(name="end_line", dtype=DataType.INT64),
            FieldSchema(name="code", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),
        ]
        schema = CollectionSchema(fields=fields, description=description)

        # ✅ IndexParams 객체 사용
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="L2",
            params={"nlist": 128}
        )

        # ✅ MilvusClient 호출
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )

        return f"✅ ver0 생성 완료 (IVF_FLAT 인덱스 적용됨)"
    except Exception as e:
        return f"❌ ver0 컬렉션 생성 실패: {e}"




# ───────────────────────────────────────────────────────
# ✅ ver1: IVF_FLAT + 단순 text 필드
def create_collection_ver1(collection_name: str, description: str = "") -> str:
    try:
        if client.has_collection(collection_name):
            return f"⚠️ 컬렉션 '{collection_name}' 이미 존재함"

        # ✅ 필드 정의
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        ]
        schema = CollectionSchema(fields=fields, description=description)

        # ✅ IndexParams (IVF_FLAT)
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="L2",
            params={"nlist": 128}
        )

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        return f"✅ ver1 생성 완료 (IVF_FLAT 인덱스 적용됨)"
    except Exception as e:
        return f"❌ ver1 컬렉션 생성 실패: {e}"


# ───────────────────────────────────────────────────────
# ✅ ver2: HNSW + 다양한 메타데이터 필드
def create_collection_ver2(collection_name: str, description: str = "") -> str:
    try:
        if client.has_collection(collection_name):
            return f"⚠️ 컬렉션 '{collection_name}' 이미 존재함"

        # ✅ 필드 정의 (ver0과 동일)
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="start_line", dtype=DataType.INT64),
            FieldSchema(name="end_line", dtype=DataType.INT64),
            FieldSchema(name="code", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),
        ]
        schema = CollectionSchema(fields=fields, description=description)

        # ✅ IndexParams (HNSW)
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="L2",
            params={"M": 16, "efConstruction": 200}
        )

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        return f"✅ ver2 생성 완료 (HNSW 인덱스 적용됨)"
    except Exception as e:
        return f"❌ ver2 컬렉션 생성 실패: {e}"


# ───────────────────────────────────────────────────────
# ✅ ver3: HNSW + 단순 text 필드
def create_collection_ver3(collection_name: str, description: str = "") -> str:
    try:
        if client.has_collection(collection_name):
            return f"⚠️ 컬렉션 '{collection_name}' 이미 존재함"

        # ✅ 필드 정의 (ver1과 동일)
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        ]
        schema = CollectionSchema(fields=fields, description=description)

        # ✅ IndexParams (HNSW)
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="L2",
            params={"M": 16, "efConstruction": 200}
        )

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        return f"✅ ver3 생성 완료 (HNSW 인덱스 적용됨)"
    except Exception as e:
        return f"❌ ver3 컬렉션 생성 실패: {e}"



###################### Delete Collection
class DeleteCollectionRequest(BaseModel):
    collection_name: str

@router.delete("/delete_collection")
async def delete_collection(req: DeleteCollectionRequest):
    try:
        # ✅ 컬렉션 존재 여부 확인
        if not client.has_collection(req.collection_name):
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{req.collection_name}' 존재하지 않음"
            }

        # ✅ MilvusClient drop
        client.drop_collection(req.collection_name)
        return {
            "success": True,
            "message": f"🗑️ 컬렉션 '{req.collection_name}' 삭제 완료"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 삭제 중 오류 발생: {e}"
        }






###################### List Collections    
@router.get("/list_collections")
async def list_collections():
    try:
        # ✅ MilvusClient로 컬렉션 목록 조회
        collections = client.list_collections()

        # ✅ 컬렉션이 하나도 없는 경우
        if not collections:
            return {
                "success": True,
                "collections": [],
                "count": 0,
                "message": "⚠️ 현재 존재하는 컬렉션이 없습니다."
            }

        # ✅ 결과 반환 (이름 리스트 포함)
        return {
            "success": True,
            "collections": collections,  # ✅ 이름 리스트 그대로 전달
            "count": len(collections),
            "message": f"✅ 총 {len(collections)}개의 컬렉션이 존재합니다: {', '.join(collections)}"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 컬렉션 조회 중 오류 발생: {e}"
        }
    


###################### View Entitiy
@router.get("/view_entities")
async def view_entities(collection_name: str = Query(..., description="Milvus 컬렉션 이름")):
    try:
        # ✅ 1. 컬렉션 존재 여부 확인
        if not client.has_collection(collection_name):
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{collection_name}' 이(가) 존재하지 않습니다."
            }

        # ✅ 2. 모든 엔티티 조회 (최대 100개)
        results = client.query(
            collection_name=collection_name,
            filter="",  # 모든 데이터 조회
            output_fields=["id", "embedding", "text"],
            limit=100
        )

        # ✅ 3. 결과 없을 경우 처리
        if not results:
            return {
                "success": True,
                "entities": [],
                "count": 0,
                "message": f"⚠️ '{collection_name}' 컬렉션에 데이터가 없습니다."
            }

        # ✅ 4. 결과 가공
        entities = []
        for item in results:
            embedding = item.get("embedding", [])
            preview = embedding[:5] if embedding else []

            entities.append({
                "id": item.get("id"),
                "text": (item.get("text") or "")[:150],
                "embedding_dim": len(embedding),
                "embedding_preview": preview
            })

        # ✅ 5. 응답 반환
        return {
            "success": True,
            "message": f"✅ '{collection_name}'에서 {len(entities)}개 엔티티 조회됨.",
            "entities": entities,
            "count": len(entities)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 조회 중 오류 발생: {e}"
        }
    




###################### Delete Entity
class DeleteEntityRequest(BaseModel):
    collection_name: str
    entity_id: str

@router.delete("/delete_entity")
async def delete_entity(req: DeleteEntityRequest):
    try:
        # ✅ 컬렉션 확인
        if not client.has_collection(req.collection_name):
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{req.collection_name}' 존재하지 않음"
            }

        # ✅ ID가 숫자 형태인지 검증
        if not req.entity_id.isdigit():
            return {
                "success": False,
                "message": "❌ 삭제 실패: 숫자 ID만 입력 가능합니다."
            }

        # ✅ 필터 조건 생성
        filter_expr = f"id in [{req.entity_id}]"

        # ✅ MilvusClient 삭제 호출
        client.delete(
            collection_name=req.collection_name,
            filter=filter_expr
        )

        return {
            "success": True,
            "message": f"✅ 엔티티 ID {req.entity_id} 삭제 완료"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 삭제 중 오류 발생: {e}"
        }



