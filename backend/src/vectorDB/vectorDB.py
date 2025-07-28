from fastapi import APIRouter, UploadFile, File, Form, Query
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction
from pydantic import BaseModel

import json, os, torch, tempfile, time

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
async def view_entities(
    collection_name: str = Query(..., description="Milvus 컬렉션 이름")
):
    try:
        # 1. 컬렉션 존재 여부 확인
        if not client.has_collection(collection_name):
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{collection_name}' 이(가) 존재하지 않습니다."
            }

        # 2. 스키마 필드 조회
        schema_info = client.describe_collection(collection_name)
        field_names = [f["name"] for f in schema_info["fields"]]

        # 3. 조회할 필드 동적 구성
        output_fields = ["id", "embedding"]
        for f in ["text", "code", "type", "name", "file_path", "start_line", "end_line"]:
            if f in field_names:
                output_fields.append(f)

        # 4. MilvusClient Query 실행
        results = client.query(
            collection_name=collection_name,
            filter="", 
            output_fields=output_fields,
            limit=100
        )

        if not results:
            return {
                "success": True,
                "entities": [],
                "count": 0,
                "message": f"⚠️ '{collection_name}' 컬렉션에 데이터가 없습니다."
            }

        # 5. 결과 가공 (numpy → float 변환 및 존재 필드만 추가)
        entities = []
        for item in results:
            embedding = item.get("embedding", [])
            embedding_preview = [float(x) for x in embedding[:5]] if embedding else []

            entity = {
                "id": item.get("id"),
                "embedding_dim": len(embedding),
                "embedding_preview": embedding_preview
            }

            # ✅ 존재하는 필드만 안전하게 추가
            for f in ["text", "code", "type", "name", "file_path", "start_line", "end_line"]:
                if f in field_names:
                    value = item.get(f)
                    if value is not None:
                        entity[f] = str(value)[:150] if isinstance(value, str) else value

            entities.append(entity)

        # 6. 응답 반환
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



#########################################################################################

@router.post("/embed_json_file")
async def embed_json_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    version: int = Form(1)
):
    try:
        # 1. JSON 파일 유효성 검사 및 저장
        if not file.filename.endswith(".json"):
            return {"success": False, "message": "❌ JSON 파일만 업로드 가능합니다."}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 2. JSON 로드
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_items = data if isinstance(data, list) else [data]

        # 3. 임베딩 수행
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-mpnet-base-v2",
            device=device
        )
        docs_as_strings = [json.dumps(item, ensure_ascii=False) for item in all_items]
        vectors = embedding_fn.encode_documents(docs_as_strings)

        if len(vectors) != len(all_items):
            return {"success": False, "message": "❌ 벡터/데이터 개수 불일치"}

        # 4. 버전에 맞는 데이터 구성
        insert_data = build_insert_data(collection_name, all_items, vectors)  # ✅ 컬렉션 이름 전달


        # 5. 컬렉션 존재 확인 후 데이터 삽입
        if not client.has_collection(collection_name):
            return {"success": False, "message": f"❌ 컬렉션 '{collection_name}' 존재하지 않음"}

        client.insert(collection_name=collection_name, data=insert_data)

        # 6. 총 엔티티 수 확인
        stats = client.get_collection_stats(collection_name)
        total_count = int(stats["row_count"])

        return {
            "success": True,
            "message": f"🎉 {len(insert_data)}개 엔티티 삽입 완료!",
            "total_entities": total_count
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 오류 발생: {e}"}

    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


def build_insert_data(collection_name: str, items: list, vectors: list):
    # 1. 컬렉션의 실제 스키마 확인
    schema_info = client.describe_collection(collection_name)
    field_names = {f["name"] for f in schema_info["fields"]}

    data = []
    for idx, item in enumerate(items):
        vec = vectors[idx]

        # 2. 기본적으로 항상 embedding 추가
        row = {"embedding": vec}

        # 3. 스키마에 존재하는 필드만 추가
        if "text" in field_names:
            row["text"] = json.dumps(item, ensure_ascii=False)

        if "code" in field_names:
            row["code"] = item.get("code", "[NO CODE]")

        if "type" in field_names:
            row["type"] = item.get("type", "unknown")

        if "name" in field_names:
            row["name"] = item.get("name", "unknown")

        if "start_line" in field_names:
            row["start_line"] = int(item.get("start_line", 0))

        if "end_line" in field_names:
            row["end_line"] = int(item.get("end_line", 0))

        if "file_path" in field_names:
            row["file_path"] = item.get("file_path", "unknown")

        data.append(row)

    return data


#########################################################################################
################# 검색 #################

# 🧠 공통 임베딩 함수
embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-mpnet-base-v2",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# ✅ 1. 기본 검색 API
@router.get("/search_basic")
async def search_basic_api(
    query_text: str = Query(..., description="검색할 텍스트"),
    collection_name: str = Query(..., description="Milvus 컬렉션 이름"),
    top_k: int = Query(5, description="검색 결과 상위 K개")
):
    try:
        start_time = time.time()

        # 🔹 임베딩 벡터 생성
        query_vector = embedding_fn.encode_queries([query_text])[0]

        # 🔹 컬렉션 필드 확인
        schema_info = client.describe_collection(collection_name)
        field_names = {f["name"] for f in schema_info["fields"]}

        output_fields = ["id", "text"] if "text" in field_names else ["id", "code", "file_path"]

        # 🔹 벡터 검색
        results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="embedding",
            search_params={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=output_fields
        )

        elapsed = time.time() - start_time
        response_results = []

        for hit in results[0]:
            entity = hit.get("entity", {})
            response_results.append({
                "id": entity.get("id"),
                "text": entity.get("text") or entity.get("code", ""),
                "distance": hit["distance"]
            })

        return {
            "success": True,
            "message": f"🔍 검색 완료 (Top-{top_k}, ⏱️ {elapsed:.2f}초)",
            "results": response_results
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 검색 오류: {e}"}


# ✅ 2. 메타데이터 필터 검색 API
@router.get("/search_with_metadata")
async def search_with_metadata_filter_api(
    query_text: str = Query(..., description="검색할 텍스트"),
    collection_name: str = Query(..., description="Milvus 컬렉션 이름"),
    metadata_filter: str = Query("", description="필터 조건 (예: type like \"%module%\")"),
    top_k: int = Query(5, description="검색 결과 상위 K개")
):
    try:
        start_time = time.time()

        query_vector = embedding_fn.encode_queries([query_text])[0]

        # 🔹 필드 설정
        output_fields = ["id", "code", "file_path", "type", "name", "start_line", "end_line"]

        # 🔹 필터 적용 벡터 검색
        results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="embedding",
            search_params={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
            filter=metadata_filter,
            output_fields=output_fields
        )

        elapsed = time.time() - start_time
        response_logs = []

        for idx, hit in enumerate(results[0], 1):
            entity = hit.get("entity", {})
            response_logs.append({
                "rank": idx,
                "id": entity.get("id"),
                "distance": hit["distance"],
                "file_path": entity.get("file_path", ""),
                "type": entity.get("type", ""),
                "name": entity.get("name", ""),
                "start_line": entity.get("start_line", "?"),
                "end_line": entity.get("end_line", "?"),
                "code_preview": (entity.get("code") or "")[:300]
            })

        return {
            "success": True,
            "message": f"🔍 메타데이터 필터 검색 완료 (Top-{top_k}, ⏱️ {elapsed:.2f}초)",
            "results": response_logs
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 검색 오류: {e}"}