"""
파싱된 레포지토리 전체를 임베딩하는 서비스
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from .embedding_service import EmbeddingService
from .exceptions import DataValidationError
from .types import EmbeddingResult

logger = logging.getLogger(__name__)


class RepositoryEmbedder:
    """파싱된 레포지토리 전체를 임베딩하는 클래스"""

    def __init__(self, base_parsed_path: str = "parsed_repository") -> None:
        """
        RepositoryEmbedder 초기화

        Args:
            base_parsed_path: 파싱된 레포지토리 기본 경로
        """
        # 프로젝트 루트 찾기
        if Path(base_parsed_path).is_absolute():
            self.base_path: Path = Path(base_parsed_path)
        else:
            current = Path.cwd()
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    self.base_path = current / base_parsed_path
                    break
                current = current.parent
            else:
                self.base_path = Path(base_parsed_path).resolve()

        self.embedding_service: EmbeddingService = EmbeddingService()

    def get_parsed_repo_path(self, repo_name: str) -> Path:
        """
        파싱된 레포지토리 경로 반환

        Args:
            repo_name: 레포지토리 이름

        Returns:
            파싱된 레포지토리 경로
        """
        return self.base_path / repo_name

    def collect_all_json_files(self, repo_name: str) -> List[Path]:
        """
        레포지토리의 모든 JSON 파일 수집

        Args:
            repo_name: 레포지토리 이름

        Returns:
            JSON 파일 경로 리스트

        Raises:
            DataValidationError: 디렉토리를 찾을 수 없거나 JSON 파일이 없을 때
        """
        parsed_path = self.get_parsed_repo_path(repo_name)

        if not parsed_path.exists():
            raise DataValidationError(
                f"Parsed repository not found: {parsed_path}. "
                f"Please run parse_repository task first."
            )

        # 재귀적으로 모든 .json 파일 수집
        json_files = list(parsed_path.rglob("*.json"))

        if not json_files:
            raise DataValidationError(
                f"No JSON files found in {parsed_path}. "
                f"Please check if parsing was successful."
            )

        logger.info(f"Found {len(json_files)} JSON files in {repo_name}")
        return json_files

    def merge_json_files(self, json_files: List[Path]) -> List[Dict[str, Any]]:
        """
        여러 JSON 파일을 하나의 리스트로 병합

        Args:
            json_files: JSON 파일 경로 리스트

        Returns:
            병합된 데이터 리스트

        Raises:
            DataValidationError: JSON 파일 읽기 실패 시
        """
        merged_data: List[Dict[str, Any]] = []

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 데이터가 리스트인 경우 extend, 딕셔너리인 경우 append
                if isinstance(data, list):
                    merged_data.extend(data)
                elif isinstance(data, dict):
                    merged_data.append(data)
                else:
                    logger.warning(f"Unexpected data type in {json_file}: {type(data)}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON file {json_file}: {e}")
                raise DataValidationError(f"Invalid JSON file: {json_file}") from e
            except Exception as e:
                logger.error(f"Failed to read file {json_file}: {e}")
                raise DataValidationError(f"Failed to read file: {json_file}") from e

        logger.info(f"Merged {len(merged_data)} total chunks from {len(json_files)} files")
        return merged_data

    def create_merged_json(self, repo_name: str) -> Path:
        """
        레포지토리의 모든 JSON을 하나로 병합하여 임시 파일 생성

        Args:
            repo_name: 레포지토리 이름

        Returns:
            병합된 JSON 파일 경로

        Raises:
            DataValidationError: 파일 생성 실패 시
        """
        # JSON 파일 수집
        json_files = self.collect_all_json_files(repo_name)

        # 데이터 병합
        merged_data = self.merge_json_files(json_files)

        # 임시 병합 파일 생성
        merged_file_path = self.base_path / f"{repo_name}_merged.json"

        try:
            with open(merged_file_path, "w", encoding="utf-8") as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Created merged JSON file: {merged_file_path}")
            return merged_file_path

        except Exception as e:
            logger.error(f"Failed to create merged JSON: {e}")
            raise DataValidationError(f"Failed to create merged JSON: {e}") from e

    def embed_repository(
        self, repo_name: str, collection_name: str, model_key: str
    ) -> EmbeddingResult:
        """
        파싱된 레포지토리 전체를 임베딩

        Args:
            repo_name: 레포지토리 이름
            collection_name: Milvus 컬렉션 이름
            model_key: 임베딩 모델 키

        Returns:
            임베딩 결과
        """
        try:
            logger.info(f"Starting repository embedding: {repo_name} -> {collection_name}")

            # 병합된 JSON 파일 생성
            merged_json_path = self.create_merged_json(repo_name)

            # 임베딩 수행
            from .types import EmbeddingInput

            input_data: EmbeddingInput = EmbeddingInput(
                json_path=str(merged_json_path),
                collection_name=collection_name,
                model_key=model_key,
            )

            result = self.embedding_service.process_embedding(input_data)

            # 임시 병합 파일 삭제 (성공 시)
            if result["success"]:
                try:
                    merged_json_path.unlink()
                    logger.info(f"Cleaned up merged JSON file: {merged_json_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete merged JSON: {e}")

            return result

        except Exception as e:
            logger.error(f"Repository embedding failed: {e}")
            return EmbeddingResult(
                success=False,
                collection_name=collection_name,
                total_documents=0,
                inserted_count=0,
                elapsed_time=0.0,
                message=None,
                error=str(e),
            )
