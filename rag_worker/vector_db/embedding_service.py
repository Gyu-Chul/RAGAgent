"""
임베딩 처리 서비스
"""

import json
import logging
import os
import time
from typing import Dict, List, Any
import torch
from rank_bm25 import BM25Okapi
from langchain_huggingface import HuggingFaceEmbeddings

from .config import EMBEDDING_MODELS
from .collection_manager import MilvusConnectionManager
from .exceptions import EmbeddingError, DataValidationError, ModelLoadError
from .types import EmbeddingInput, EmbeddingResult

logger = logging.getLogger(__name__)


class BM25ModelCache:
    """BM25 모델 캐시 관리 클래스"""

    _cache: Dict[str, BM25Okapi] = {}

    @classmethod
    def get(cls, collection_name: str) -> BM25Okapi:
        """
        캐시에서 BM25 모델 가져오기

        Args:
            collection_name: 컬렉션 이름

        Returns:
            BM25 모델 (없으면 None)
        """
        return cls._cache.get(collection_name)

    @classmethod
    def set(cls, collection_name: str, model: BM25Okapi) -> None:
        """
        캐시에 BM25 모델 저장

        Args:
            collection_name: 컬렉션 이름
            model: BM25 모델
        """
        cls._cache[collection_name] = model
        logger.info(f"✅ BM25 model cached for collection: {collection_name}")

    @classmethod
    def has(cls, collection_name: str) -> bool:
        """
        캐시에 모델이 있는지 확인

        Args:
            collection_name: 컬렉션 이름

        Returns:
            존재 여부
        """
        return collection_name in cls._cache


class DenseEmbedder:
    """밀집 벡터 임베딩 처리 클래스"""

    def __init__(self, model_key: str) -> None:
        """
        DenseEmbedder 초기화

        Args:
            model_key: 모델 키 (config.EMBEDDING_MODELS에 정의된 키)

        Raises:
            ModelLoadError: 모델 로드 실패 시
        """
        self.model_key: str = model_key
        self.model_config: Dict[str, Any] = EMBEDDING_MODELS.get(model_key)

        if not self.model_config:
            raise ModelLoadError(f"Model config not found for key: {model_key}")

        try:
            # 디버깅: 환경 확인
            import sys
            logger.info(f"🔍 Python executable: {sys.executable}")
            logger.info(f"🔍 PyTorch version: {torch.__version__}")
            logger.info(f"🔍 CUDA available: {torch.cuda.is_available()}")
            logger.info(f"🔍 CUDA version: {torch.version.cuda if hasattr(torch.version, 'cuda') else 'N/A'}")

            device: str = "cuda" if torch.cuda.is_available() else "cpu"

            if device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                logger.info(f"🚀 Loading dense embedding model on GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            else:
                logger.info(f"⚠️ Loading dense embedding model on CPU (GPU not available)")

            # safetensors 강제 사용을 위한 환경 변수 설정
            import os
            os.environ["SAFETENSORS_FAST_GPU"] = "1"

            self.embedder: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
                model_name=self.model_config["model_name"],
                model_kwargs={
                    "device": device,
                    "trust_remote_code": True
                },
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info(f"✅ Dense embedding model loaded: {model_key} on {device.upper()}")

        except Exception as e:
            import traceback
            logger.error(f"Failed to load dense embedding model: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise ModelLoadError(f"Failed to load model: {e}") from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트를 밀집 벡터로 변환

        Args:
            texts: 텍스트 리스트

        Returns:
            밀집 벡터 리스트
        """
        import gc
        import torch

        result = self.embedder.embed_documents(texts)

        # 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        return result


class SparseEmbedder:
    """희소 벡터 임베딩 처리 클래스 (BM25)"""

    def __init__(self, tokenized_corpus: List[List[str]]) -> None:
        """
        SparseEmbedder 초기화

        Args:
            tokenized_corpus: 토큰화된 문서 리스트
        """
        self.bm25: BM25Okapi = BM25Okapi(tokenized_corpus)

    def embed_documents(
        self, tokenized_corpus: List[List[str]]
    ) -> List[Dict[int, float]]:
        """
        토큰화된 문서를 희소 벡터로 변환

        Args:
            tokenized_corpus: 토큰화된 문서 리스트

        Returns:
            희소 벡터 리스트 (딕셔너리 형태)
        """
        sparse_vectors: List[Dict[int, float]] = []

        for doc_tokens in tokenized_corpus:
            doc_scores = self.bm25.get_scores(doc_tokens)
            sparse_vec = {i: score for i, score in enumerate(doc_scores) if score > 0}
            sparse_vectors.append(sparse_vec)

        return sparse_vectors


class EmbeddingService:
    """임베딩 처리 통합 서비스 클래스"""

    def __init__(self, batch_size: int = 256, embedding_batch_size: int = 12) -> None:
        """
        EmbeddingService 초기화

        Args:
            batch_size: Milvus 삽입 배치 크기
            embedding_batch_size: 임베딩 생성 배치 크기 (메모리 절약)
        """
        self.client = MilvusConnectionManager.get_client()
        self.batch_size: int = batch_size
        self.embedding_batch_size: int = embedding_batch_size

    def process_embedding(self, input_data: EmbeddingInput) -> EmbeddingResult:
        """
        JSON 파일에서 데이터를 읽어 임베딩 후 Milvus에 저장

        Args:
            input_data: 임베딩 작업 입력

        Returns:
            임베딩 결과
        """
        start_time: float = time.time()

        try:
            # 0. 컬렉션 존재 확인 및 생성
            from .collection_manager import CollectionManager
            from .config import EMBEDDING_MODELS

            collection_manager = CollectionManager()
            collection_name = input_data["collection_name"]

            if not collection_manager.exists(collection_name):
                logger.info(f"Collection '{collection_name}' not found. Creating...")
                model_config = EMBEDDING_MODELS.get(input_data["model_key"])
                dim = model_config["dim"]

                result = collection_manager.create_collection(
                    collection_name=collection_name,
                    dim=dim,
                    description=f"Auto-created for embedding task"
                )

                if not result["success"]:
                    raise EmbeddingError(f"Failed to create collection: {result['error']}")

                logger.info(f"✅ Collection '{collection_name}' created successfully")

            # 1. 데이터 로딩
            logger.info(f"▶️ Starting embedding process for collection: {collection_name}")
            texts, metadata_list = self._load_data(input_data["json_path"])

            if not texts:
                raise DataValidationError("No valid documents found in JSON file")

            # 2. 희소 벡터 생성
            logger.info("Generating sparse vectors (BM25)...")
            tokenized_corpus = [doc.split(" ") for doc in texts]
            sparse_embedder = SparseEmbedder(tokenized_corpus)
            sparse_vectors = sparse_embedder.embed_documents(tokenized_corpus)

            # BM25 모델 캐싱
            BM25ModelCache.set(input_data["collection_name"], sparse_embedder.bm25)
            logger.info("✅ Sparse vectors generated and BM25 model cached")

            # 3. 밀집 벡터 생성 (배치로 나눠서 처리)
            logger.info(f"Generating dense vectors ({len(texts)} documents) in batches of {self.embedding_batch_size}...")
            dense_embedder = DenseEmbedder(input_data["model_key"])

            dense_vectors: List[List[float]] = []
            for batch_idx, i in enumerate(range(0, len(texts), self.embedding_batch_size), 1):
                batch_end = min(i + self.embedding_batch_size, len(texts))
                batch_texts = texts[i:batch_end]

                logger.info(f"  - Embedding batch {batch_idx}/{(len(texts)-1)//self.embedding_batch_size + 1}: {i+1}~{batch_end}/{len(texts)}")
                batch_vectors = dense_embedder.embed_documents(batch_texts)
                dense_vectors.extend(batch_vectors)

                # 배치마다 메모리 정리
                del batch_vectors
                del batch_texts
                import gc
                gc.collect()

            logger.info("✅ Dense vectors generated")

            # 4. Milvus에 배치 삽입
            inserted_count = self._batch_insert(
                collection_name=input_data["collection_name"],
                texts=texts,
                metadata_list=metadata_list,
                dense_vectors=dense_vectors,
                sparse_vectors=sparse_vectors,
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"🎉 Embedding completed: {inserted_count} documents inserted in {elapsed_time:.2f}s"
            )

            return EmbeddingResult(
                success=True,
                collection_name=input_data["collection_name"],
                total_documents=len(texts),
                inserted_count=inserted_count,
                elapsed_time=elapsed_time,
                message=f"Successfully embedded {inserted_count} documents",
                error=None,
            )

        except (DataValidationError, ModelLoadError, EmbeddingError, Exception) as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Embedding failed: {e}")

            return EmbeddingResult(
                success=False,
                collection_name=input_data.get("collection_name", ""),
                total_documents=0,
                inserted_count=0,
                elapsed_time=elapsed_time,
                message=None,
                error=str(e),
            )

    def _load_data(self, json_path: str) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        JSON 파일에서 데이터 로딩

        Args:
            json_path: JSON 파일 경로

        Returns:
            (텍스트 리스트, 메타데이터 리스트)

        Raises:
            DataValidationError: 파일을 찾을 수 없거나 형식이 잘못된 경우
        """
        if not os.path.exists(json_path):
            raise DataValidationError(f"File not found: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                items = json.load(f)

            texts: List[str] = []
            metadata_list: List[Dict[str, Any]] = []

            for item in items:
                code = item.get("code")
                if code and code.strip():
                    texts.append(code)
                    metadata_list.append({k: v for k, v in item.items() if k != "code"})

            logger.info(f"Loaded {len(texts)} valid documents from {json_path}")
            return texts, metadata_list

        except json.JSONDecodeError as e:
            raise DataValidationError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise DataValidationError(f"Failed to load data: {e}") from e

    def _batch_insert(
        self,
        collection_name: str,
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
        dense_vectors: List[List[float]],
        sparse_vectors: List[Dict[int, float]],
    ) -> int:
        """
        배치 단위로 데이터 삽입

        Args:
            collection_name: 컬렉션 이름
            texts: 텍스트 리스트
            metadata_list: 메타데이터 리스트
            dense_vectors: 밀집 벡터 리스트
            sparse_vectors: 희소 벡터 리스트

        Returns:
            삽입된 문서 수

        Raises:
            EmbeddingError: 삽입 실패 시
        """
        total_inserted = 0

        for i in range(0, len(texts), self.batch_size):
            batch_end = min(i + self.batch_size, len(texts))
            logger.info(f"  - Inserting batch: {i+1} ~ {batch_end} / {len(texts)}")

            # 배치 데이터 조립
            data_to_insert: List[Dict[str, Any]] = []
            for j in range(i, batch_end):
                row = metadata_list[j].copy()
                row["text"] = texts[j]
                row["dense"] = dense_vectors[j]
                row["sparse"] = sparse_vectors[j]

                # _source_file 필드 추가 (file_path에서 파일명만 추출)
                if "file_path" in row:
                    import os
                    row["_source_file"] = os.path.basename(row["file_path"])
                else:
                    row["_source_file"] = "unknown"

                data_to_insert.append(row)

            # 배치 삽입
            try:
                res = self.client.insert(collection_name=collection_name, data=data_to_insert)
                total_inserted += res["insert_count"]
                logger.info(f"  ✅ Batch inserted successfully (Total: {total_inserted})")

            except Exception as e:
                logger.error(f"❌ Batch insertion failed at index {i}: {e}")
                raise EmbeddingError(f"Batch insertion failed: {e}") from e

        return total_inserted
