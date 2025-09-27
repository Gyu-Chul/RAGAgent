# RAGIT - RAG with Gateway-Backend Architecture

RAGIT은 마이크로서비스 아키텍처 기반의 자체 호스팅 RAG (Retrieval-Augmented Generation) 시스템입니다.

## 프로젝트 개요

RAGIT은 다음과 같은 핵심 특징을 가진 RAG 시스템입니다:

- **마이크로서비스 아키텍처**: Gateway-Backend 패턴으로 확장 가능한 구조
- **통합 SDK**: 모든 기능을 `ragit` 명령어로 통합 관리
- **Docker 지원**: 개발/프로덕션 환경 분리 배포
- **실시간 모니터링**: 서비스 상태 및 리소스 모니터링

## 프로젝트 구조

```
RAGIT/
├── backend/                 # FastAPI 기반 REST API 서버
│   ├── models/              # SQLAlchemy 데이터 모델
│   ├── services/            # 비즈니스 로직 서비스
│   ├── routers/             # API 라우터
│   └── main.py              # FastAPI 애플리케이션
│
├── frontend/                # NiceGUI 기반 웹 인터페이스
│   ├── components/          # UI 컴포넌트
│   ├── pages/               # 페이지 모듈
│   ├── services/            # 프론트엔드 서비스
│   └── main.py              # NiceGUI 애플리케이션
│
├── gateway/                 # API 게이트웨이 및 프록시
│   ├── middleware/          # 미들웨어
│   ├── config.py            # 게이트웨이 설정
│   └── main.py              # 게이트웨이 서버
│
├── rag_worker/              # Celery 기반 RAG 처리 워커
│   ├── tasks/               # 백그라운드 작업
│   ├── models/              # RAG 모델 관리
│   └── main.py              # Celery 애플리케이션
│
├── ragit_sdk/               # 통합 관리 SDK
│   ├── cli.py               # Click 기반 CLI 인터페이스
│   ├── process_manager.py   # 로컬 프로세스 관리
│   ├── docker_manager.py    # Docker 컨테이너 관리
│   ├── config.py            # 설정 관리 시스템
│   ├── logger.py            # 통합 로깅 시스템
│   └── utils.py             # 유틸리티 함수
│
├── docs/                    # 프로젝트 문서
├── scripts/                 # 관리 스크립트 (레거시)
├── milvus/                  # Milvus 벡터 데이터베이스 설정
├── sample/                  # 샘플 데이터 및 예제
│
├── docker-compose.yml       # 개발 환경 Docker 설정
├── docker-compose.prod.yml  # 프로덕션 환경 Docker 설정
├── Dockerfile               # Docker 이미지 빌드 설정
├── pyproject.toml           # 프로젝트 설정 및 의존성
├── install.sh               # 자동 설치 스크립트
└── CLAUDE.md                # 개발 코딩 규칙
```

## 아키텍처

RAGIT은 다음과 같은 마이크로서비스 아키텍처로 구성됩니다:

```
사용자 → Frontend → Gateway → Backend → Database/Cache
                              ↓
                          RAG Worker → Vector DB
```

### 핵심 컴포넌트

- **Frontend (NiceGUI)**: 사용자 인터페이스 및 웹 애플리케이션
- **Gateway**: 요청 라우팅, 로드 밸런싱, 인증 처리
- **Backend (FastAPI)**: 핵심 비즈니스 로직 및 REST API
- **RAG Worker (Celery)**: 비동기 RAG 처리 및 벡터 검색
- **PostgreSQL**: 구조화된 데이터 저장
- **Redis**: 캐싱 및 메시지 큐
- **Milvus**: 벡터 데이터베이스 (RAG 검색용)

## 빠른 시작

### Docker 설치 (권장)

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 자동 설치
chmod +x install.sh
./install.sh
```

### SDK 사용

```bash
# 의존성 설치
uv sync

# 서비스 시작
ragit start

# 상태 확인
ragit status
```

### 접속 정보

- **웹 인터페이스**: http://localhost:8000
- **백엔드 API**: http://localhost:8001
- **게이트웨이**: http://localhost:8080

## 문서

자세한 설치 및 사용 방법은 다음 문서를 참조하세요:

- **[설치 가이드](docs/installation.md)** - 상세한 설치 및 설정 방법
- **[SDK 사용 가이드](docs/sdk-usage.md)** - RAGIT SDK 완전 활용법
- **[문서 목록](docs/README.md)** - 모든 문서 색인
