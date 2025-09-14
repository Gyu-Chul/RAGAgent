import os
import json
import torch
from pymilvus import connections, Collection
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction

def embed_json_file(json_path: str, collection_name: str) -> str:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🧠 Using device: {device}")

    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-mpnet-base-v2",
        device=device
    )

    # ─── 1. JSON 로딩 ───────────────────────
    if not os.path.exists(json_path):
        return f"❌ 파일이 존재하지 않음: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_items = data if isinstance(data, list) else [data]
    print(f"📦 JSON에서 {len(all_items)}개 객체 로드")

    # ─── 2. 벡터화 ───────────────────────────
    docs_as_strings = [json.dumps(item, ensure_ascii=False) for item in all_items]
    code_texts = [item.get("code", "[NO CODE]") for item in all_items]
    vectors = embedding_fn.encode_documents(docs_as_strings)

    if len(vectors) != len(code_texts):
        return "❌ 벡터/코드 길이 불일치"

    # ─── 3. Milvus 삽입 ─────────────────────
    connections.connect(alias="default", host="127.0.0.1", port=19530)
    collection = Collection(name=collection_name)
    collection.load()

    insert_data = [vectors, code_texts]
    collection.insert(insert_data)
    collection.flush()

    return f"🎉 삽입 완료! {len(vectors)}개 엔티티가 추가됨. 현재 개수: {collection.num_entities}"


# 🔧 CLI 전용 진입점 (웹에서는 import만 하도록)
if __name__ == '__main__':
    from src.milvus.list_collections import list_collections
    list_collections()
    path = input("\n📂 JSON 경로 입력: ").strip()
    name = input("🎯 컬렉션 이름 입력: ").strip()
    result = embed_json_file(path, name)
    print(result)
