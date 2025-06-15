import os
import json
import torch
from pymilvus import connections, Collection
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction
from list_collections import list_collections

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🧠 Using device: {device}")

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-mpnet-base-v2",
    device=device
)

# ─── 1. JSON 파일 로딩 ─────────────────────────────
json_paths = []
if os.path.exists("main.json"):
    json_paths.append("main.json")

for root, _, files in os.walk("dummy"):
    for fname in files:
        if fname.endswith(".json"):
            json_paths.append(os.path.join(root, fname))

all_items = []
for path in json_paths:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            all_items.extend(data)
        elif isinstance(data, dict):
            all_items.append(data)

print(f"📦 총 {len(all_items)}개의 JSON 객체를 수집했습니다.")

# ─── 2. 임베딩 및 text 추출 ───────────────────────
docs_as_strings = [
    json.dumps(item, ensure_ascii=False)
    for item in all_items
]

code_texts = [
    item.get("code", "[NO CODE]")  # 없을 경우 대비
    for item in all_items
]

vectors = embedding_fn.encode_documents(docs_as_strings)
assert len(vectors) == len(code_texts)

# ─── 3. Milvus 연결 및 컬렉션 선택 ───────────────
connections.connect(alias="default", host="127.0.0.1", port=19530)
list_collections()
collection_name = input("\n🎯 삽입할 Milvus 컬렉션 이름을 입력하세요: ").strip()
collection = Collection(name=collection_name)
collection.load()

# ─── 4. Milvus에 삽입 ────────────────────────────
insert_data = [
    vectors,
    code_texts
]

print(f"📨 Milvus 컬렉션 '{collection_name}'에 데이터를 삽입 중...")
res = collection.insert(insert_data)
collection.flush()

print(f"🎉 삽입 완료! 총 {len(vectors)}개의 엔티티가 추가되었습니다.")
print(f"📊 현재 엔티티 수: {collection.num_entities}")
