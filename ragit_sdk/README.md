# RAGIT SDK

RAG with Gateway-Backend Architecture를 위한 통합 관리 SDK

## 📁 디렉토리 구조

```
ragit_sdk/
├── __init__.py           # 패키지 초기화 및 주요 export
├── cli.py                # CLI 진입점 (ragit 명령어)
├── config.py             # 설정 관리 (RagitConfig)
├── logger.py             # 로깅 유틸리티
├── utils.py              # 공통 유틸리티 함수
│
├── core/                 # 핵심 기능 모듈
│   ├── __init__.py
│   ├── docker_manager.py  # Docker 컨테이너 관리
│   └── process_manager.py # 프로세스 생명주기 관리
│
└── tests/                # 테스트 및 검증 스크립트
    ├── __init__.py
    ├── check_milvus.py    # Milvus DB 데이터 확인
    ├── test_git_worker.py # Git Worker 통합 테스트
    └── test_search_only.py # 검색 기능 단독 테스트
```

## 🚀 주요 기능

### Core Modules
- **DockerManager**: Docker Compose 기반 컨테이너 관리
- **ProcessManager**: 백그라운드 프로세스 생명주기 관리
- **RagitConfig**: 환경별 설정 관리

### CLI Commands
```bash
# 인프라 시작 (PostgreSQL, Redis, Milvus)
ragit infra

# 서비스 관리
ragit start [--mode all|dev]
ragit stop
ragit restart
ragit status

# 테스트
ragit test milvus   # Milvus 데이터 확인
ragit test search   # 검색 기능 테스트
ragit test worker   # Git Worker 전체 테스트

# Docker 관리
ragit docker build [--mode dev|prod]
ragit docker start [--mode dev|prod]
ragit docker stop
ragit docker logs [--service SERVICE]
ragit docker ps
```

## 📦 설치

```bash
# 개발 모드로 설치
pip install -e .

# 프로덕션 설치
pip install .
```

## 🧪 테스트 실행

### 방법 1: CLI 사용
```bash
ragit test worker  # Git Worker 전체 테스트
ragit test search  # 검색 기능 테스트
ragit test milvus  # Milvus 데이터 확인
```

### 방법 2: 직접 실행
```bash
python -m ragit_sdk.tests.test_git_worker
python -m ragit_sdk.tests.test_search_only
python -m ragit_sdk.tests.check_milvus
```

## 🏗️ 아키텍처 원칙

이 SDK는 다음 원칙을 준수합니다:

1. **단일 책임 원칙 (SRP)**: 각 클래스는 하나의 책임만 가짐
2. **인터페이스 분리 원칙 (ISP)**: 필요한 기능만 노출
3. **타입 안정성**: 모든 함수/메서드에 타입 어노테이션 필수

## 📝 사용 예시

### Python에서 직접 사용
```python
from ragit_sdk import RagitConfig, ProcessManager, DockerManager

# 설정 로드
config = RagitConfig()

# 프로세스 관리
process_mgr = ProcessManager(config)
process_mgr.start_all()

# Docker 관리
docker_mgr = DockerManager(config)
docker_mgr.start_local_infrastructure()
```

### CLI 사용
```bash
# 로컬 개발 환경 시작
ragit infra

# Celery Worker 실행 (별도 터미널)
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info --pool=solo

# 테스트 실행
ragit test worker
```

## 🔧 개발

### 새로운 테스트 추가
1. `ragit_sdk/tests/`에 테스트 스크립트 작성
2. `ragit_sdk/cli.py`의 `test` 그룹에 명령어 추가
3. `ragit_sdk/tests/__init__.py`의 `__all__`에 추가

### 새로운 Core 기능 추가
1. `ragit_sdk/core/`에 모듈 작성
2. `ragit_sdk/core/__init__.py`에서 export
3. `ragit_sdk/__init__.py`에서 재export (필요시)

## 📄 라이선스

MIT License
