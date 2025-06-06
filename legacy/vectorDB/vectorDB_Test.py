# ─── 라이브러리 불러오기 ─────────────────────────
import ast
import tokenize, io
import torch
from transformers import RobertaTokenizer, RobertaModel
import numpy as np
from pathlib import Path

import chromadb
from sentence_transformers import CrossEncoder

# ─── 0. 디바이스 설정 ───────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ─── 1. 모델 로드 & GPU로 이동 ────────────────────────
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model     = RobertaModel.from_pretrained("microsoft/codebert-base") \
                  .to(device).eval()

# RoBERTa 계열 max tokens
MAX_TOKENS = model.config.max_position_embeddings - 2  # e.g. 512
OVERLAP    = 128

# ─── 2. ChromaDB 세팅 ───────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    "code_snippets",
    metadata={
      "hnsw:space": "cosine",
      "hnsw:construction_ef": 200,
      "hnsw:M": 32,
      "hnsw:search_ef": 50,
      "hnsw:num_threads": 4,
    }
)

# ─── 헬퍼 함수 정의 ───────────────────────────────────

def extract_comment_map(source: str):
    """{라인번호: [주석,…]} 맵 생성"""
    cm = {}
    reader = io.StringIO(source).readline
    for tok in tokenize.generate_tokens(reader):
        if tok.type == tokenize.COMMENT:
            cm.setdefault(tok.start[0], []).append(tok.string)
    return cm

def ast_extract_functions_and_classes(source: str):
    """
    [(name, start, end, code, docstring), …] for def/class
    """
    tree = ast.parse(source)
    chunks = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name  = node.name
            start, end = node.lineno, node.end_lineno
            code = ast.get_source_segment(source, node)
            doc  = ast.get_docstring(node) or ""
            chunks.append((name, start, end, code, doc))
    return chunks

def extract_top_level_statement_chunks(source: str):
    """
    함수·클래스 외 최상위 노드를
    연속 라인 단위로 그룹핑한 [(name, s, e, code, "")…] 를 반환.
    """
    tree = ast.parse(source)
    stmts = []
    # 1) 함수/클래스 외 노드 추출
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # 모듈 docstring(최상단 Expr(Str)) 생략
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom,
                             ast.Assign, ast.AugAssign, ast.AnnAssign,
                             ast.Expr)):
            s, e = node.lineno, node.end_lineno
            code = ast.get_source_segment(source, node).rstrip()
            stmts.append((s, e, code))

    # 2) 연속된 라인끼리 그룹핑
    stmts.sort(key=lambda x: x[0])
    grouped = []
    cur_s, cur_e, cur_codes = None, None, []
    for s, e, code in stmts:
        if cur_s is None:
            # 첫 그룹 시작
            cur_s, cur_e, cur_codes = s, e, [code]
        elif s <= cur_e + 1:
            # 이전 그룹과 라인이 연속되면 합치기
            cur_e = max(cur_e, e)
            cur_codes.append(code)
        else:
            # 연속 끊기면 이전 그룹 저장 후 새 그룹 시작
            grouped.append((cur_s, cur_e, "\n".join(cur_codes)))
            cur_s, cur_e, cur_codes = s, e, [code]
    if cur_s is not None:
        grouped.append((cur_s, cur_e, "\n".join(cur_codes)))

    # 3) 반환 포맷에 맞추기
    #    name="" 으로 표시하면 모듈 최상위임을 알 수 있습니다.
    return [("", s, e, code, "") for s,e,code in grouped]


def augment_chunk(name, start, end, code, doc, comment_map):
    """
    docstring + 해당 라인의 주석 + 코드 를 합침
    """
    parts = []
    if doc:
        parts.append(f'"""{doc}"""')
    for ln in range(start, end+1):
        for c in comment_map.get(ln, []):
            parts.append(c)
    parts.append(code)
    return "\n".join(parts)

def sliding_window(text, tok, max_tokens, overlap):
    toks = tok.encode(text)
    subchunks, i, L = [], 0, len(toks)
    while i < L:
        j = min(i + max_tokens, L)
        sub = tok.decode(toks[i:j])
        subchunks.append(sub)
        if j == L:
            break
        i += (max_tokens - overlap)
    return subchunks

# ─── 3. 파일별 인덱싱 함수 ───────────────────────────
def index_file(path: Path):
    source = path.read_text(encoding="utf-8")
    comment_map = extract_comment_map(source)

    # 3.1 함수·클래스 단위 청크
    ast_chunks = ast_extract_functions_and_classes(source)

    # 3.2 최상위 문장 단위 청크
    stmt_chunks = extract_top_level_statement_chunks(source)

    all_chunks = ast_chunks + stmt_chunks

    ids, embs, metas, docs = [], [], [], []
    for name, s, e, code, doc in all_chunks:
        full = augment_chunk(name, s, e, code, doc, comment_map)

        # 3.3 토큰 검사 & 슬라이딩
        tok_cnt = len(tokenizer.encode(full))
        subs = [full] if tok_cnt <= MAX_TOKENS else sliding_window(full, tokenizer, MAX_TOKENS, OVERLAP)

        for idx, sub in enumerate(subs):
            # 3.4 임베딩 추출
            inp = tokenizer(
                sub,
                return_tensors="pt",
                truncation=True,
                padding="max_length",
                max_length=MAX_TOKENS
            ).to(device)
            with torch.no_grad():
                out = model(**inp)
                v = out.last_hidden_state[:,0,:].cpu().numpy().squeeze()
            v = v / np.linalg.norm(v)

            # 메타데이터
            uid = f"{path.name}:{name or 'stmt'}:{s}-{e}:{idx}"
            meta = {
                "file": path.name,
                "function": name,       # "" 이면 최상위 문장
                "start_line": s,
                "end_line": e
            }

            ids.append(uid)
            embs.append(v.tolist())
            metas.append(meta)
            docs.append(sub)

    collection.upsert(ids=ids, embeddings=embs, metadatas=metas, documents=docs)
    print(f"[Indexed] {path.name} → {len(ids)} fragments")

# ─── 4. 전체 파일 인덱싱 ─────────────────────────────
for py in Path(".").glob("*.py"):
    index_file(py)

# ─── 5. 질문 처리 & Cross-Encoder 재순위 ─────────────
def answer_question(question: str, top_k=5):
    # 5.1 질문 임베딩
    qinp = tokenizer(
        question,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128
    ).to(device)
    with torch.no_grad():
        qout = model(**qinp)
        qv = qout.last_hidden_state[:,0,:].cpu().numpy().squeeze()
    qv = qv / np.linalg.norm(qv)

    # 5.2 1단계 검색 (함수/문장 구분)
    if any(kw in question.lower() for kw in ("initialize", "connect", "client")):
        filt = None  # 전역·함수 모두 검색
    else:
        filt = {"function": {"$ne": ""}}  # 함수 블록만

    query_args = dict(
        query_embeddings=[qv.tolist()],
        n_results=top_k * 5,
        include=["metadatas", "documents"]
    )
    if filt is not None:
        query_args["where"] = filt

    res1 = collection.query(**query_args)

    # 5.3 Cross-Encoder 재순위
    ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2").to(device)
    pairs  = [(question, doc) for doc in res1["documents"][0]]
    scores = ce.predict(pairs)

    ranked = sorted(
        zip(res1["metadatas"][0], res1["documents"][0], scores),
        key=lambda x: x[2], reverse=True
    )

    # 5.4 최종 Top-k 출력
    for i, (meta, doc, sc) in enumerate(ranked[:top_k], 1):
        print(f"[{i}] {meta['file']}::{meta['function'] or '<module>'} "
              f"(lines {meta['start_line']}-{meta['end_line']}) → {sc:.4f}")
        print(doc, "\n")

if __name__ == "__main__":
    print("\n=== 질문 예시 ===")
    answer_question("How do I initialize the database connection?")
