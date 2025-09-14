from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction
from pydantic import BaseModel
from pathlib import Path
from typing import Any, Dict, List

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

# ─────────────────────────────────────────────────────────────────────────────
# 설정값 (환경에 맞게 조절)
DEFAULT_EMBED_BATCH = 256                     # 임베딩 배치 크기
DEFAULT_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024  # gRPC 64MB보다 여유 있게 50MB 목표
# ─────────────────────────────────────────────────────────────────────────────
# 상단 설정
HARD_CAP_CHARS = 65000  # 스키마 못 읽을 때 최후 안전값(VarChar 65535 하한선 근처)

def _dtype_is_varchar(dt) -> bool:
    # dt가 enum, int, str 어느 형태든 'varchar' 판별
    s = str(dt).lower()
    return ("varchar" in s) or (s.strip() in {"23", "varchar", "data_type.varchar"})

def _get_maxlen_from_field(f: dict) -> int | None:
    # params or type_params 안에서 max_length 추출 (str일 수 있음)
    for key in ("params", "type_params"):
        params = f.get(key) or {}
        if "max_length" in params:
            try:
                return int(params["max_length"])
            except Exception:
                pass
    return None

def get_varchar_limits(schema_info: dict) -> dict[str, int]:
    """필드별 VarChar max_length 매핑. 못 찾으면 None (나중에 하드캡 적용)."""
    limits = {}
    for f in schema_info.get("fields", []):
        if _dtype_is_varchar(f.get("data_type")):
            ml = _get_maxlen_from_field(f)
            if isinstance(ml, int) and ml > 0:
                limits[f["name"]] = ml
    return limits



def truncate_utf8(s: str, max_bytes: int) -> str:
    """UTF-8 바이트 기준 안전 절단(멀티바이트 깨짐 방지)."""
    if s is None or max_bytes is None:
        return s
    b = s.encode("utf-8")
    if len(b) <= max_bytes:
        return s
    ell = "…[TRUNCATED]"
    ell_b = ell.encode("utf-8")
    keep = max_bytes - len(ell_b)
    if keep <= 0:
        return b[:max_bytes].decode("utf-8", errors="ignore")
    return b[:keep].decode("utf-8", errors="ignore") + ell


def truncate_chars(s: str, max_chars: int | None) -> str:
    if s is None or max_chars is None:
        return s
    if len(s) <= max_chars:
        return s
    ell = "…[TRUNCATED]"
    keep = max(0, max_chars - len(ell))
    return (s[:keep] + ell) if keep > 0 else s[:max_chars]



def approx_row_bytes(vec, item: dict, include_text: bool) -> int:
    """gRPC 페이로드 근사치: 벡터(float32) + 텍스트(옵션) + 오버헤드."""
    vec_bytes = (len(vec) * 4) if hasattr(vec, "__len__") else 0  # float32 가정
    text_bytes = 0
    if include_text:
        try:
            text_bytes = len(json.dumps(item, ensure_ascii=False).encode("utf-8"))
        except Exception:
            text_bytes = 0
    return vec_bytes + text_bytes + 512  # 헤더/필드 오버헤드 여유치


def build_row_for_schema(item: dict, vec, field_names: set[str], varchar_limits: dict[str, int]):
    row = {"embedding": vec}

    if "text" in field_names:
        raw = json.dumps(item, ensure_ascii=False)
        ml = varchar_limits.get("text", HARD_CAP_CHARS)
        row["text"] = truncate_chars(raw, ml)

    if "code" in field_names:
        raw = item.get("code", "[NO CODE]")
        ml = varchar_limits.get("code", HARD_CAP_CHARS)
        row["code"] = truncate_chars(raw, ml)

    if "type" in field_names:
        raw = item.get("type", "unknown")
        ml = varchar_limits.get("type")  # 일반적으로 작음, 없으면 제한 없음
        row["type"] = truncate_chars(raw, ml) if ml else raw

    if "name" in field_names:
        raw = item.get("name", "unknown")
        ml = varchar_limits.get("name")
        row["name"] = truncate_chars(raw, ml) if ml else raw

    if "file_path" in field_names:
        raw = item.get("file_path", "unknown")
        ml = varchar_limits.get("file_path")
        row["file_path"] = truncate_chars(raw, ml) if ml else raw

    if "start_line" in field_names:
        row["start_line"] = int(item.get("start_line", 0))
    if "end_line" in field_names:
        row["end_line"] = int(item.get("end_line", 0))

    # (선택) 잘림 여부 표시
    if "is_truncated" in field_names:
        def over(name: str) -> bool:
            if name not in row:
                return False
            lm = varchar_limits.get(name, HARD_CAP_CHARS if name in ("text", "code") else None)
            return lm is not None and len(row[name]) >= lm
        row["is_truncated"] = bool(over("text") or over("code"))

    return row


#################################################### 업로드를 통한 json 읽기 방법
# @router.post("/embed_json_file")
# async def embed_json_file(
#     file: UploadFile = File(...),
#     collection_name: str = Form(...),
#     embed_batch_size: int = Form(DEFAULT_EMBED_BATCH),              # 임베딩 배치
#     max_payload_bytes: int = Form(DEFAULT_MAX_PAYLOAD_BYTES),       # gRPC 페이로드 컷
# ):
#     """
#     대규모 JSON:
#     - 임베딩: embed_batch_size로 쪼개서 처리
#     - 삽입: gRPC 페이로드를 max_payload_bytes 이하가 되도록 바이트 기준 분할
#     - VarChar: 스키마 max_length에 맞춰 UTF-8 안전 절단
#     - 시간: 임베딩/삽입/전체 경과 포함해 message로 반환
#     """
#     try:
#         total_start = time.perf_counter()

#         # 1) 파일 검증 + 임시 저장
#         if not file.filename.endswith(".json"):
#             return {"success": False, "message": "❌ JSON 파일만 업로드 가능합니다."}

#         with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
#             tmp.write(await file.read())
#             tmp_path = tmp.name

#         # 2) JSON 로드
#         with open(tmp_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         all_items = data if isinstance(data, list) else [data]
#         total_items = len(all_items)
#         if total_items == 0:
#             return {"success": False, "message": "⚠️ 비어있는 JSON입니다."}

#         # 3) 환경 준비
#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         embedding_fn = SentenceTransformerEmbeddingFunction(
#             model_name="sentence-transformers/all-mpnet-base-v2",
#             device=device
#         )

#         if not client.has_collection(collection_name):
#             return {"success": False, "message": f"❌ 컬렉션 '{collection_name}' 존재하지 않음"}

#         # 스키마 1회 조회
#         schema_info = client.describe_collection(collection_name)
#         field_names = {f["name"] for f in schema_info.get("fields", [])}
#         varchar_limits = get_varchar_limits(schema_info)

#         embed_elapsed_total = 0.0
#         insert_elapsed_total = 0.0
#         inserted_count = 0

#         # 4) 배치 임베딩 루프
#         for start in range(0, total_items, embed_batch_size):
#             end = min(start + embed_batch_size, total_items)
#             batch_items = all_items[start:end]
#             docs_as_strings = [json.dumps(item, ensure_ascii=False) for item in batch_items]

#             # 임베딩 시간 측정 (CUDA 동기화로 정확도↑)
#             if device == "cuda":
#                 torch.cuda.synchronize()
#             t0 = time.perf_counter()
#             vectors = embedding_fn.encode_documents(docs_as_strings)
#             if device == "cuda":
#                 torch.cuda.synchronize()
#             embed_elapsed_total += (time.perf_counter() - t0)

#             if len(vectors) != len(batch_items):
#                 return {"success": False, "message": "❌ 벡터/데이터 개수 불일치(배치)"}

#             # 5) 삽입: 바이트 기준으로 분할 전송
#             buffer_rows = []
#             buffer_bytes = 0

#             include_text = ("text" in field_names)

#             for i, item in enumerate(batch_items):
#                 row = build_row_for_schema(item, vectors[i], field_names, varchar_limits)
#                 row_bytes = approx_row_bytes(vectors[i], item, include_text=include_text)

#                 # 현재 버퍼 + 새 행이 한도를 넘으면 먼저 flush
#                 if buffer_rows and (buffer_bytes + row_bytes) > max_payload_bytes:
#                     t1 = time.perf_counter()
#                     client.insert(collection_name=collection_name, data=buffer_rows)
#                     insert_elapsed_total += (time.perf_counter() - t1)
#                     inserted_count += len(buffer_rows)
#                     buffer_rows = []
#                     buffer_bytes = 0

#                 buffer_rows.append(row)
#                 buffer_bytes += row_bytes

#             # 잔여 flush
#             if buffer_rows:
#                 t1 = time.perf_counter()
#                 client.insert(collection_name=collection_name, data=buffer_rows)
#                 insert_elapsed_total += (time.perf_counter() - t1)
#                 inserted_count += len(buffer_rows)

#         # 6) 총 엔티티 수
#         stats = client.get_collection_stats(collection_name)
#         total_count = int(stats["row_count"])

#         total_elapsed = time.perf_counter() - total_start

#         # search_basic_api 스타일의 message
#         return {
#             "success": True,
#             "message": (
#                 f"🎉 {inserted_count}개 엔티티 삽입 완료 "
#                 f"(⏱️ 임베딩 {embed_elapsed_total:.2f}s, 삽입 {insert_elapsed_total:.2f}s, 전체 {total_elapsed:.2f}s; "
#                 f"배치 embed={embed_batch_size}, payload≤{max_payload_bytes // (1024*1024)}MB)"
#             ),
#             "total_entities": total_count
#         }

#     except Exception as e:
#         return {"success": False, "message": f"❌ 오류 발생: {e}"}

#     finally:
#         if 'tmp_path' in locals() and os.path.exists(tmp_path):
#             os.remove(tmp_path)

##########################################################################################################################################################
############################################################################# 실제 임베딩 api
##########################################################################################################################################################
class EmbedJsonRequest(BaseModel):
    json_path: str
    collection_name: str
    embed_batch_size: int = DEFAULT_EMBED_BATCH
    max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES

@router.post("/embed_json_file")
async def embed_json_file(req: EmbedJsonRequest):
    """
    Content-Type: application/json 요청 전용
    기존 로직 유지, 파일 업로드 대신 서버에 존재하는 JSON 파일 경로를 받음
    """
    try:
        total_start = time.perf_counter()

        # 1) 파일 경로 검증
        if not req.json_path.endswith(".json"):
            return {"success": False, "message": "❌ JSON 파일만 처리 가능합니다."}
        if not os.path.exists(req.json_path):
            return {"success": False, "message": f"❌ 파일이 존재하지 않음: {req.json_path}"}

        # 2) JSON 로드
        with open(req.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_items = data if isinstance(data, list) else [data]
        total_items = len(all_items)
        if total_items == 0:
            return {"success": False, "message": "⚠️ 비어있는 JSON입니다."}

        # 3) 환경 준비
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-mpnet-base-v2",
            device=device
        )

        if not client.has_collection(req.collection_name):
            return {"success": False, "message": f"❌ 컬렉션 '{req.collection_name}' 존재하지 않음"}

        # 스키마 1회 조회
        schema_info = client.describe_collection(req.collection_name)       ### 해당하는 DB의 정보 추출 - 어떤 field가 있는지 즉, 어떤 메타데이터가 들어갈 수 있는지 정보 포함
        field_names = {f["name"] for f in schema_info.get("fields", [])}    ### 그 정보에서 field name을 가져와서 임베딩할 때 어떤 구조로 임베딩할 것인지 자동 결정 (분기 없이 버전 처리 성공)
        varchar_limits = get_varchar_limits(schema_info)

        embed_elapsed_total = 0.0
        insert_elapsed_total = 0.0
        inserted_count = 0

        # 4) 배치 임베딩 루프
        for start in range(0, total_items, req.embed_batch_size):
            print("임베딩 작업중 입니다.")
            print(start,total_items)
            end = min(start + req.embed_batch_size, total_items)
            batch_items = all_items[start:end]
            docs_as_strings = [json.dumps(item, ensure_ascii=False) for item in batch_items]

            if device == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            vectors = embedding_fn.encode_documents(docs_as_strings)
            if device == "cuda":
                torch.cuda.synchronize()
            embed_elapsed_total += (time.perf_counter() - t0)

            if len(vectors) != len(batch_items):
                return {"success": False, "message": "❌ 벡터/데이터 개수 불일치(배치)"}

            buffer_rows = []
            buffer_bytes = 0
            include_text = ("text" in field_names)

            for i, item in enumerate(batch_items):
                row = build_row_for_schema(item, vectors[i], field_names, varchar_limits)
                row_bytes = approx_row_bytes(vectors[i], item, include_text=include_text)

                if buffer_rows and (buffer_bytes + row_bytes) > req.max_payload_bytes:
                    t1 = time.perf_counter()
                    client.insert(collection_name=req.collection_name, data=buffer_rows)
                    insert_elapsed_total += (time.perf_counter() - t1)
                    inserted_count += len(buffer_rows)
                    buffer_rows = []
                    buffer_bytes = 0

                buffer_rows.append(row)
                buffer_bytes += row_bytes

            if buffer_rows:
                t1 = time.perf_counter()
                client.insert(collection_name=req.collection_name, data=buffer_rows)
                insert_elapsed_total += (time.perf_counter() - t1)
                inserted_count += len(buffer_rows)

        stats = client.get_collection_stats(req.collection_name)
        total_count = int(stats["row_count"])

        total_elapsed = time.perf_counter() - total_start

        return {
            "success": True,
            "message": (
                f"🎉 {inserted_count}개 엔티티 삽입 완료 "
                f"(⏱️ 임베딩 {embed_elapsed_total:.2f}s, 삽입 {insert_elapsed_total:.2f}s, 전체 {total_elapsed:.2f}s; "
                f"배치 embed={req.embed_batch_size}, payload≤{req.max_payload_bytes // (1024*1024)}MB)"
            ),
            "total_entities": total_count
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 오류 발생: {e}"}

##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################

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
    top_k: int = Query(3, description="검색 결과 상위 K개")
):
    try:
        print("시작해보자.")
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
    metadata_filter: str = Query("type like \"%module%\"", description="필터 조건 (예: type like \"%module%\")"),
    top_k: int = Query(3, description="검색 결과 상위 K개")
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

            # 📌 줄바꿈·폰트 고정용 문자열 생성
            formatted = "\n".join([
                f"[{idx}] ID: {entity.get('id', '')} | 유사도: {hit['distance']:.4f}",
                f"📂 Path: {entity.get('file_path', '')}",
                f"🔖 Type: {entity.get('type', '')} | Name: {entity.get('name', '')}",
                f"📏 Lines: {entity.get('start_line', '?')} - {entity.get('end_line', '?')}",
                "💻 Code Preview:",
                f"```python\n{(entity.get('code') or '')[:500]}\n```",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ])

            response_logs.append({
                "rank": idx,
                "id": entity.get("id"),
                "distance": hit["distance"],
                "file_path": entity.get("file_path", ""),
                "type": entity.get("type", ""),
                "name": entity.get("name", ""),
                "start_line": entity.get("start_line", "?"),
                "end_line": entity.get("end_line", "?"),
                "code_preview": (entity.get("code") or "")[:300],
                "log_str": formatted  # 🔹 로그 출력을 위한 문자열
            })

        return {
            "success": True,
            "message": f"🔍 메타데이터 필터 검색 완료 (Top-{top_k}, ⏱️ {elapsed:.2f}초)",
            "results": response_logs
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 검색 오류: {e}"}

    


############################### total json 임시 생성

# ── 프로젝트 루트 자동 탐색 ─────────────────────────────
def find_project_root(marker_dir_name="git-ai") -> Path:
    """marker_dir_name 디렉토리까지 상위로 탐색하여 Path 반환"""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if parent.name == marker_dir_name:
            return parent
    raise RuntimeError(f"❌ 프로젝트 루트 디렉토리 '{marker_dir_name}'를 찾을 수 없습니다.")

PROJECT_ROOT = find_project_root("git-ai")
TARGET_ROOT = PROJECT_ROOT / "git-agent" / "parsed_repository"

def iter_json_items(p: Path):
    """파일이 리스트면 원소를, 오브젝트면 그 자체를 yield. 실패하면 에러 dict."""
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            yield data
    except Exception as e:
        yield {"_error": f"failed_to_parse:{p.name}", "_reason": str(e)}

@router.post("/merge-json")
def merge_json(repo: str):
    target_dir = (TARGET_ROOT / repo).resolve()

    # TARGET_ROOT 바깥을 가리키는 우회 방지
    if TARGET_ROOT not in target_dir.parents and target_dir != TARGET_ROOT:
        raise HTTPException(status_code=400, detail="Invalid repo path.")

    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Not found: {target_dir}")

    json_files = sorted(target_dir.rglob("*.json"))
    if not json_files:
        raise HTTPException(status_code=404, detail=f"No JSON files under: {target_dir}")

    out_path = (target_dir / f"{repo}__all.json").resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    skipped = 0
    merged: List[Dict[str, Any]] = []

    for jp in json_files:
        for item in iter_json_items(jp):
            if isinstance(item, dict) and "_error" in item:
                skipped += 1
                continue
            if isinstance(item, dict):
                item.setdefault("_source_file", str(jp.relative_to(target_dir)))
            merged.append(item)
            total += 1

    with out_path.open("w", encoding="utf-8") as out:
        json.dump(merged, out, ensure_ascii=False, indent=2)

    return {
        "repo": repo,
        "out_path": str(out_path),
        "files_scanned": len(json_files),
        "merged_items": total,
        "skipped": skipped
    }
