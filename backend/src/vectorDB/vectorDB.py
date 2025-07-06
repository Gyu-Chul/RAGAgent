from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel
from pymilvus import connections, Collection, utility, FieldSchema, CollectionSchema, DataType
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction
import os
import json
import tempfile
import torch

router = APIRouter()

###################### Connection Test
@router.get("/connection_test")
def connection_test():
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        collections = utility.list_collections()
        return {
            "success": True,
            "message": "✅ Milvus 연결 성공!",
            "collections": collections
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Milvus 연결 실패: {e}"
        }
    


###################### Count Entities
@router.get("/count_entities")
def count_entities(collection_name: str = Query(..., description="Milvus 컬렉션 이름")):
    try:
        collection = Collection(name=collection_name)
        count = collection.num_entities
        return {
            "success": True,
            "collection": collection_name,
            "entity_count": count,
            "message": f'📊 Collection "{collection_name}" has {count} entities.'
        }
    except MilvusException as e:
        return {
            "success": False,
            "collection": collection_name,
            "error_type": "MilvusException",
            "message": f'❌ 엔티티 개수 조회 실패: {e}'
        }
    except Exception as e:
        return {
            "success": False,
            "collection": collection_name,
            "error_type": "UnknownError",
            "message": f'❌ 알 수 없는 오류: {e}'
        }
    


###################### Create Collection
class CreateCollectionRequest(BaseModel):
    collection_name: str
    description: str = ""

@router.post("/create_collection")
def create_collection(req: CreateCollectionRequest):
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        if utility.has_collection(req.collection_name):
            return {
                "success": False,
                "message": f"⚠️ 컬렉션 '{req.collection_name}' 이미 존재함"
            }

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
            description=req.description
        )

        collection = Collection(name=req.collection_name, schema=schema)
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
                "metric_type": "L2"
            }
        )

        return {
            "success": True,
            "message": f"✅ 컬렉션 '{req.collection_name}' 생성 및 인덱스 구성 완료"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 컬렉션 생성 실패: {e}"
        }



###################### Delete Collection
class DeleteCollectionRequest(BaseModel):
    collection_name: str

@router.delete("/delete_collection")
def delete_collection(req: DeleteCollectionRequest):
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        if utility.has_collection(req.collection_name):
            utility.drop_collection(req.collection_name)
            return {
                "success": True,
                "message": f"🗑️ 컬렉션 '{req.collection_name}' 삭제 완료"
            }
        else:
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{req.collection_name}' 존재하지 않음"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 오류 발생: {e}"
        }







###################### Delete Entity
class DeleteEntityRequest(BaseModel):
    collection_name: str
    entity_id: str

@router.delete("/delete_entity")
def delete_entity(req: DeleteEntityRequest):
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        collection = Collection(name=req.collection_name)
        collection.load()

        if not req.entity_id.isdigit():
            return {
                "success": False,
                "message": "❌ 삭제 실패: 숫자 ID만 입력 가능합니다."
            }

        expr = f"id in [{req.entity_id}]"
        collection.delete(expr=expr)
        collection.flush()

        return {
            "success": True,
            "message": f"✅ 엔티티 ID {req.entity_id} 삭제 완료"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 삭제 중 오류 발생: {e}"
        }




@router.post("/embed_json_file")
async def embed_json_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...)
):
    try:
        # ─── 1. 업로드된 파일을 임시 저장 ──────────────
        if not file.filename.endswith(".json"):
            return {"success": False, "message": "❌ JSON 파일만 업로드 가능합니다."}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # ─── 2. JSON 로드 및 전처리 ────────────────
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_items = data if isinstance(data, list) else [data]
        docs_as_strings = [json.dumps(item, ensure_ascii=False) for item in all_items]
        code_texts = [item.get("code", "[NO CODE]") for item in all_items]

        # ─── 3. 임베딩 수행 ───────────────────────
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-mpnet-base-v2",
            device=device
        )
        vectors = embedding_fn.encode_documents(docs_as_strings)

        if len(vectors) != len(code_texts):
            return {
                "success": False,
                "message": "❌ 벡터/코드 길이 불일치"
            }

        # ─── 4. Milvus 삽입 ──────────────────────
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        collection = Collection(name=collection_name)
        collection.load()

        collection.insert([vectors, code_texts])
        collection.flush()

        return {
            "success": True,
            "message": f"🎉 삽입 완료! {len(vectors)}개 엔티티가 추가됨.",
            "total_entities": collection.num_entities
        }

    except Exception as e:
        return {"success": False, "message": f"❌ 오류 발생: {e}"}

    finally:
        # ─── 5. 임시 파일 정리 ───────────────────
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)



###################### List Collections    
@router.get("/list_collections")
def list_collections():
    # 1. Milvus 연결 (이미 연결돼 있다면 재연결 X)
    if not connections.has_connection("default"):
        try:
            connections.connect(
                alias="default",
                host="127.0.0.1",
                port=19530
            )
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Milvus 연결 실패: {e}"
            }

    # 2. 컬렉션 리스트 조회
    try:
        collections = utility.list_collections()
    except MilvusException as e:
        return {
            "success": False,
            "message": f"❌ 컬렉션 조회 중 오류 발생: {e}"
        }

    # 3. 결과 반환
    if not collections:
        return {
            "success": True,
            "collections": [],
            "message": "⚠️ 현재 존재하는 컬렉션이 없습니다."
        }

    return {
        "success": True,
        "collections": collections,
        "count": len(collections),
        "message": f"✅ 총 {len(collections)}개의 컬렉션이 존재합니다."
    }




###################### View Entitiy
@router.get("/view_entities")
def view_entities(collection_name: str = Query(..., description="Milvus 컬렉션 이름")):
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host="127.0.0.1", port=19530)

        if not utility.has_collection(collection_name):
            return {
                "success": False,
                "message": f"❌ 컬렉션 '{collection_name}' 이(가) 존재하지 않습니다."
            }

        collection = Collection(name=collection_name)
        collection.load()

        results = collection.query(
            expr="",  # 모든 엔티티
            output_fields=["id", "embedding", "text"],
            limit=100
        )

        if not results:
            return {
                "success": True,
                "entities": [],
                "message": f"⚠️ '{collection_name}' 컬렉션에 데이터가 없습니다."
            }

        # 응답 포맷 정리
        entities = []
        for item in results:
            embedding = item["embedding"]
            preview = [float(x) for x in embedding[:5]]  # 🔥 numpy → float 변환

            entities.append({
                "id": item.get("id", None),
                "text": item.get("text", "")[:150],
                "embedding_dim": len(embedding),
                "embedding_preview": preview
            })
        return {
            "success": True,
            "message": f"✅ '{collection_name}'에서 {len(results)}개 엔티티 조회됨.",
            "entities": entities,
            "count": len(entities)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 조회 중 오류 발생: {e}"
        }