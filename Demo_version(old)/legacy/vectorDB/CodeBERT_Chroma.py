# ─ 라이브러리 불러오기 ─────────────────────────
import ast, torch
from transformers import RobertaTokenizer, RobertaModel
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

import chromadb
from chromadb.config import Settings

from sentence_transformers import CrossEncoder ## 크로스-인코더 사용용


# ─── 0. 디바이스 설정 ───────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ─── 1. 모델 로드 & GPU로 이동 ────────────────────────
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")
model.to(device)
model.eval()

# ─ 코드 읽기 ─────────────────────────────────────
FILE_PATH = "example.py"
with open(FILE_PATH, encoding="utf-8") as f:
    code = f.read()
lines = code.splitlines()

# ─ AST 함수 블록 + 슬라이딩 윈도우 추출 ─────────────
tree = ast.parse(code)
func_blocks = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        s, e = node.lineno-1, node.end_lineno
        func_blocks.append({
            "code": "\n".join(lines[s:e]),
            "file": FILE_PATH,
            "function": node.name,
            "start_line": s+1,
            "end_line": e
        })

window_blocks = []
W, S = 5, 3
for i in range(0, len(lines), S):
    j = min(i+W, len(lines))
    window_blocks.append({
        "code": "\n".join(lines[i:j]),
        "file": FILE_PATH,
        "function": None,
        "start_line": i+1,
        "end_line": j
    })

all_blocks = func_blocks + window_blocks

# ─ 임베딩 생성 ────────────────────────────────────
entries = []
for blk in all_blocks:
    # ── 3. 토크나이즈 & GPU로 옮기기 ─────────────
    inputs = tokenizer(
        blk["code"],
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=512
    )
    # 모든 텐서를 device로 이동
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # ── 4. 임베딩 추출 ─────────────────────────
    with torch.no_grad():
        outputs = model(**inputs)
        emb = outputs.last_hidden_state[:, 0, :]  # [1, 768]

    # ── 5. CPU로 옮기고 NumPy 변환 ───────────────
    emb_cpu = emb.squeeze(0).cpu().numpy()      # [768]

    entries.append({
        "embedding": emb_cpu,
        "file":      blk["file"],
        "function":  blk["function"],
        "start_line": blk["start_line"],
        "end_line":   blk["end_line"],
    })

print(f"총 {len(entries)}개 블록 임베딩 생성 완료.")


# ─ 2) DataFrame ───────────────────────────────────
# df_rows = []
# for e in entries:
#     row = {
#         "file": e["file"],
#         "func": e["function"] or "–",
#         "start": e["start_line"],
#         "end":   e["end_line"],
#     }
#     for i in range(5):
#         row[f"dim_{i}"] = float(e["embedding"][i])
#     df_rows.append(row)

# df = pd.DataFrame(df_rows)
# print("\n==== DataFrame Preview ====")
# print(df)

# ─── 4. 벡터 전처리: L2 정규화 후 저장 ─────────────────
for e in entries:
    vec = e["embedding"]
    e["embedding"] = vec / np.linalg.norm(vec)    # ← 정규화

#------------------------------------------------------#
#-----------------------chromadb-----------------------#
#------------------------------------------------------#


# ─── 5. ChromaDB 세팅 ───────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection(
    "code_snippets",
    metadata={
      "hnsw:space": "cosine",
      "hnsw:construction_ef": 200,
      "hnsw:M": 32,
      "hnsw:search_ef": 50,
      "hnsw:num_threads": 4,
    }
)

# ─── 6. 업서트 ───────────────────────────────────────
ids        = [f"{e['file']}:{e['start_line']}-{e['end_line']}" for e in entries]
embeddings = [e["embedding"] for e in entries]
metadatas  = [
    {
      "file":       e["file"],
      "function":   e["function"] or "",
      "start_line": e["start_line"],
      "end_line":   e["end_line"]
    }
    for e in entries
]
docs = [e["code"] for e in all_blocks]

collection.upsert(ids=ids, embeddings=embeddings,
                  metadatas=metadatas, documents=docs)

# ─── 7. 질문 임베딩 & 전처리 ─────────────────────────
question = "When the player_x_p change at main?"
q_inp = tokenizer(question, return_tensors="pt",
                  truncation=True, padding="max_length", max_length=128)
q_inp = {k:v.to(device) for k,v in q_inp.items()}

with torch.no_grad():
    q_out     = model(**q_inp)
    q_emb_raw = q_out.last_hidden_state[:,0,:].squeeze(0).cpu().numpy()

q_emb = q_emb_raw / np.linalg.norm(q_emb_raw)  # ← 정규화

# ─── 8. 동적 필터링 & 2단계 검색 ───────────────────────
# 질문 키워드 기반으로 함수 vs 전역 블록 선택
keywords_for_global = ["import", "global", "main"]
if any(kw in question.lower() for kw in keywords_for_global):
    # 전역 블록 검색 (function 필드가 빈 문자열인 항목)
    filter_cond = {"function": ""}
else:
    # 함수 블록 검색 (function 필드가 비어있지 않은 항목)
    filter_cond = {"function": {"$ne": ""}}

# 1단계 검색: 선택된 블록 타입 전체에서 top 10
res1 = collection.query(
    query_embeddings=[q_emb],
    n_results=10,
    where=filter_cond,
    include=["metadatas", "documents"]
)

# 2단계: 함수 블록일 때만, 각 함수별로 세부 윈도우 재검색
candidates = []
if filter_cond == {"function": {"$ne": ""}}:
    # 함수 블록이므로 상위 5개 함수 추출 후 재검색
    func_hits = list(zip(res1["metadatas"][0], res1["documents"][0]))[:5]
    for meta, _ in func_hits:
        fname = meta["function"]
        res2 = collection.query(
            query_embeddings=[q_emb],
            n_results=3,
            where={"function": fname},
            include=["metadatas","documents"]
        )
        candidates += list(zip(res2["metadatas"][0], res2["documents"][0]))
else:
    # 전역 블록이므로 1단계 결과를 곧장 후보로
    candidates = list(zip(res1["metadatas"][0], res1["documents"][0]))


# ─── 9. 후처리: Cross-Encoder 재순위 ─────────────────
# 크로스-인코더 모델 로드 (MS MARCO 등, 원하는 모델 사용)
ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2").to(device)

# (질문, 코드블록) 페어 생성
pairs = [(question, doc) for _, doc in candidates]
scores = ce.predict(pairs)  # shape: (len(pairs),)

# 점수 기반으로 내림차순 정렬
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

# ─── 10. 최종 상위 5개 출력 ────────────────────────────
print("=== 최종 Top 5 ===")
for i, ((meta, doc), score) in enumerate(ranked[:5], 1):
    print(f"[{i}] 파일: {meta['file']}  함수: {meta['function']} "
          f"(lines {meta['start_line']}-{meta['end_line']})")
    print(f"Score: {score:.4f}")
    print(doc, "\n")

#------------------------------------------------------#
#-----------------------chromadb-----------------------#
#------------------------------------------------------#