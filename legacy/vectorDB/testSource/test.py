import json
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ─── 데이터 로드 & 임베딩 모델 초기화 ─────────────────────────
#FILE_PATH = "Chunk_graphicinterface_class.json"
#FILE_PATH = "Chunk_commit.json"
FILE_PATH = "Chunk_README.json"
with open(FILE_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device=device)

# ─── 모든 청크 임베딩 & DB 설정 ─────────────────────────
texts = [c["code"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="main_vectors",
    metadata={"hnsw:space": "cosine"}
)

ids = [f"{c['file_path']}:{c['start_line']}-{c['end_line']}" for c in chunks]
metadatas = [
    {
        "type":       c["type"],
        "subtype":    c.get("subtype", ""),
        "section":    c.get("section", ""),
        "start_line": c["start_line"],
        "end_line":   c["end_line"],
        "commit_id":  c.get("commit_id", ""),
        "file_path":  c["file_path"]
    }
    for c in chunks
]
documents = texts

collection.upsert(ids=ids,
                  embeddings=embeddings.tolist(),
                  metadatas=metadatas,
                  documents=documents)

print("✅ Upsert complete.")

# ─── 질문 임베딩 및 유사도 검색 ─────────────────────────────
#question = "What will be selected if my choice is 3"
#question = "How much of offset will be resonable?"
#question = "Which library is used in this py?"


question = " How can I Activate the Virtual Environment"

q_vec = model.encode([question], show_progress_bar=False)[0]

res = collection.query(
    query_embeddings=[q_vec],
    n_results=5,
    include=["metadatas", "documents", "distances"]
)

# ─── 유사도 점수 출력 ─────────────────────────────────────
print(f"\n🔍 질문: {question}\n")
for idx, (md, doc, dist) in enumerate(zip(res["metadatas"][0], res["documents"][0], res["distances"][0]), start=1):
    print(f"[{idx}] 유사도: {1 - dist:.4f} (distance: {dist:.4f})")
    print(f"    파일: {md['file_path']} lines {md['start_line']}-{md['end_line']}")
    snippet = doc.splitlines()[0]
    print(f"    code: \n{doc}\n")
