import os

# Milvus 서버 연결 정보 (환경변수로부터 읽기, 기본값은 로컬)
MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT: str = os.getenv("MILVUS_PORT", "19530")
MILVUS_URI: str = f"http://{MILVUS_HOST}:{MILVUS_PORT}"

# --- 모델 설정 중앙 관리 ---
EMBEDDING_MODELS = {
    # 기존 모델 (영어 검색 최적화 모델)
    "mpnet-base-v2": {
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "dim": 768,
        "kwargs": {}
    },
    # 코드 검색 최적화 모델 (CodeXEmbed)
    "sfr-code-400m": {
        "model_name": "Salesforce/SFR-Embedding-Code-400M_R",
        "dim": 1024,
        "kwargs": {"trust_remote_code": True}
    }
}

# 기본으로 사용할 모델의 '키'를 지정
DEFAULT_MODEL_KEY = "sfr-code-400m"

# 기본 컬렉션 이름
DEFAULT_COLLECTION_NAME = "langchain_default_collection"

# 임베딩할 테스트 데이터 파일 경로
TEST_DATA_PATH = "test_data.json"