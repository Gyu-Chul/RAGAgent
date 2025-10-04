# RAGIT 개발자 가이드

RAGIT 프로젝트를 로컬에서 개발하고 수정하는 방법과 SDK 사용법을 설명합니다.

> 💡 **고급 개발자를 위한 팁**: 각 서비스를 개별적으로 실행하고 디버깅하는 방법은 [고급 개발자 가이드](developer-guide-advanced.md)를 참조하세요.

## 📋 목차

- [개발 환경 설정](#개발-환경-설정)
- [로컬 설치 및 실행](#로컬-설치-및-실행)
- [SDK 사용법](#sdk-사용법)
- [개발 워크플로우](#개발-워크플로우)
- [프로그래밍 API](#프로그래밍-api)
- [테스트 및 디버깅](#테스트-및-디버깅)
- [고급 개발 팁](#고급-개발-팁)

## 💻 개발 환경 설정

RAGIT을 개발하기 위해 필요한 환경을 설정합니다.

### 시스템 요구사항

- **Python**: 3.11+
- **Docker**: 최신 버전 (PostgreSQL과 Redis 실행용)
- **Docker Compose**: v2.0+
- **Node.js**: 18+ (일부 도구 사용 시)
- **Git**: 최신 버전

### 1. Python 환경 설정

```bash
# Python 3.11+ 설치 확인
python3 --version

# UV 패키지 매니저 설치 (권장)
# MacOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 윈도우
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   

# 또는 pip 사용
python3 -m pip install --upgrade pip
```

### 2. Docker 설치

RAGIT은 PostgreSQL과 Redis를 Docker 컨테이너로 실행합니다.

```bash
# Docker 설치 확인
docker --version
docker compose version

# Docker가 실행 중인지 확인
docker ps

# Docker 설치가 필요한 경우:
# - Windows/Mac: Docker Desktop 설치 (https://www.docker.com/products/docker-desktop)
# - Linux: Docker Engine 설치 (https://docs.docker.com/engine/install/)
```

> **참고**: PostgreSQL과 Redis를 별도로 설치할 필요가 없습니다. `ragit start` 명령어가 자동으로 Docker 컨테이너를 실행합니다.

## 🚀 로컬 설치 및 실행

### 1. 프로젝트 클론 및 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 가상환경 생성 (UV 사용)
uv venv
source .venv/bin/activate  # Linux/macOS
# 또는 .venv\Scripts\activate  # Windows

# 의존성 설치 (개발 모드)
uv sync --dev

# 또는 pip 사용
pip install -e .
```

### 2. 환경 설정

RAGIT은 `.env.local` 파일을 사용하여 로컬 개발 환경을 설정합니다 (이미 생성되어 있음):

```bash
# .env.local 파일 내용 확인
cat .env.local

# 필요시 수정
# Local Development 환경 설정 파일
SECRET_KEY=your-secret-key-for-local-development
ENVIRONMENT=development
DEBUG=true

# Database (로컬 Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragit
POSTGRES_DB=ragit
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis (로컬 Docker)
REDIS_URL=redis://localhost:6379/0

# API 설정
CORS_ORIGINS=["http://localhost:8000", "http://localhost:8001", "http://localhost:8080"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# 서비스 포트
FRONTEND_PORT=8000
BACKEND_PORT=8001
GATEWAY_PORT=8080
```

> **참고**: PostgreSQL과 Redis는 Docker 컨테이너로 실행되므로, DATABASE_URL과 REDIS_URL은 localhost로 설정되어 있습니다.

### 3. RAGIT SDK 설치 확인

```bash
# SDK 설치 확인
ragit --version

# 설정 확인
ragit config

# 사용 가능한 명령어 확인
ragit --help
```

## 🎯 SDK 사용법

### 기본 CLI 명령어

```bash
# 도움말 보기
ragit --help

# 버전 확인
ragit --version

# 설정 정보 확인
ragit config
```

### 로컬 서비스 관리

```bash
# 🚀 모든 서비스 시작 (Docker 인프라 포함)
# - PostgreSQL, Redis 컨테이너 자동 시작
# - Backend, Gateway, RAG Worker, Frontend 순차 시작
ragit start --mode all

# 개발 모드로 시작 (더 상세한 로그)
ragit start --mode dev

# 개별 서비스 시작 (Docker 인프라는 수동 시작 필요)
ragit-process start-backend
ragit-process start-frontend
ragit-process start-gateway
ragit-process start-rag-worker

# 🛑 서비스 중지 (Docker 인프라 포함)
# - 모든 서비스 종료
# - PostgreSQL, Redis 컨테이너 자동 중지
ragit stop

# 서비스 재시작
ragit restart

# 서비스 상태 확인
ragit status

# 실시간 모니터링
ragit monitor
```

### 개발 환경 특화 기능

```bash
# 상세 로그와 함께 시작
ragit start --mode dev --verbose

# 특정 서비스만 재시작 (개발 중)
ragit-process restart-backend
ragit-process restart-frontend

# 포트 충돌 확인
ragit config --check-ports
```

### Docker 인프라 관리

RAGIT은 PostgreSQL과 Redis를 Docker로 자동 관리합니다:

```bash
# ✅ 자동 관리 (권장)
# ragit start 시 자동으로 Docker 인프라 시작
ragit start

# ragit stop 시 자동으로 Docker 인프라 중지
ragit stop

# 🔧 수동 관리 (고급 사용자)
# PostgreSQL, Redis만 별도로 시작
docker compose -f docker-compose.local.yml up -d

# PostgreSQL, Redis 중지
docker compose -f docker-compose.local.yml down

# 컨테이너 상태 확인
docker ps | grep ragit

# 컨테이너 로그 확인
docker logs ragit-postgres
docker logs ragit-redis

# 전체 Docker 시스템 관리 (모든 서비스 컨테이너화)
ragit docker build --mode dev
ragit docker start --mode dev
ragit docker logs --service backend
ragit docker stop --mode dev
```

## 🔄 개발 워크플로우

### 일반적인 개발 프로세스

```bash
# 1. 개발 환경 시작 (Docker 인프라 + 모든 서비스)
ragit start --mode dev

# 2. 코드 수정 작업
# - backend/, frontend/, gateway/, rag_worker/ 디렉토리에서 개발

# 3. 변경사항 테스트
ragit-process restart-backend  # 백엔드 변경 시
ragit-process restart-frontend # 프론트엔드 변경 시

# 4. 로그 확인
ragit monitor

# 5. 테스트 실행 (섹션 참조)
pytest tests/

# 6. 개발 완료 후 정리 (서비스 + Docker 인프라 모두 종료)
ragit stop
```

> **자동화 포인트**: `ragit start`는 다음을 순차적으로 실행합니다:
> 1. Docker Compose로 PostgreSQL, Redis 컨테이너 시작
> 2. 컨테이너 헬스체크 완료 대기
> 3. Backend → Gateway → RAG Worker → Frontend 순서로 서비스 시작

### 브랜치 기반 개발

```bash
# 새 기능 브랜치 생성
git checkout -b feature/new-functionality

# 개발 환경 시작
ragit start --mode dev

# 개발 및 테스트
# ... 코드 작업 ...

# 변경사항 커밋
git add .
git commit -m "feat: Add new functionality"

# 메인 브랜치로 이동하여 통합 테스트
git checkout main
ragit restart
```

### 핫 리로드 개발

일부 서비스는 코드 변경 시 자동으로 재시작됩니다:

- **Backend (FastAPI)**: `--reload` 옵션으로 자동 재시작
- **Frontend (NiceGUI)**: 개발 모드에서 자동 리로드
- **Gateway**: 수동 재시작 필요
- **RAG Worker**: 수동 재시작 필요

## 🧪 테스트 및 디버깅

### 단위 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 모듈 테스트
pytest tests/backend/
pytest tests/frontend/

# 커버리지와 함께 테스트
pytest --cov=backend --cov=frontend

# 상세 출력으로 테스트
pytest -v -s
```

### 통합 테스트

```bash
# 서비스 시작 후 통합 테스트
ragit start --mode dev

# API 엔드포인트 테스트
curl http://localhost:8001/health
curl http://localhost:8080/health

# 자동화된 통합 테스트
pytest tests/integration/
```

### 로그 및 디버깅

```bash
# 실시간 로그 모니터링
ragit monitor

# 로그 파일 확인
tail -f logs/ragit_$(date +%Y%m%d).log

# 에러 로그만 확인
tail -f logs/ragit_error_$(date +%Y%m%d).log

# 특정 서비스 로그
tail -f logs/backend.log
tail -f logs/frontend.log
```

### 개발 도구

```bash
# 코드 품질 검사
black .                    # 코드 포매팅
isort .                    # import 정렬
flake8 .                   # 린트 검사

# 타입 체크 (mypy 설치 시)
mypy backend/ frontend/

# 의존성 검사
uv sync --check
```

## 💡 고급 개발 팁

### 프로젝트 구조 이해

```
RAGIT/
├── backend/                    # FastAPI 백엔드
├── frontend/                   # NiceGUI 프론트엔드
├── gateway/                    # API 게이트웨이
├── rag_worker/                 # Celery 워커
├── ragit_sdk/                  # SDK 및 CLI
├── docs/                       # 문서
├── tests/                      # 테스트
├── logs/                       # 로그 파일
├── data/                       # 데이터 파일
├── docker-compose.yml          # 전체 시스템 Docker Compose
├── docker-compose.local.yml    # 로컬 개발용 (PostgreSQL, Redis만)
├── pyproject.toml
├── .env                        # Docker 환경 설정
└── .env.local                  # 로컬 개발 환경 설정
```

### SDK 아키텍처

RAGIT SDK의 주요 구성 요소:

```
ragit_sdk/
├── cli.py              # 메인 CLI 인터페이스
├── config.py           # 설정 관리
├── process_manager.py  # 로컬 프로세스 관리
├── docker_manager.py   # Docker 컨테이너 관리
├── logger.py           # 로깅 시스템
└── utils.py           # 유틸리티 함수
```

### 개발 시 주의사항

1. **Docker 실행**: Docker Desktop/Engine이 실행 중이어야 함
2. **포트 충돌**:
   - 5432 (PostgreSQL), 6379 (Redis) - Docker 컨테이너
   - 8000 (Frontend), 8001 (Backend), 8080 (Gateway) - 로컬 프로세스
3. **환경 변수**: `.env.local` 파일의 설정값 확인
4. **로그 레벨**: 개발 시 `DEBUG` 레벨 사용 권장
5. **의존성 관리**: `uv sync` 또는 `pip install -e .` 정기 실행
6. **컨테이너 정리**: 개발 완료 후 `ragit stop`으로 Docker 리소스 정리

### 성능 최적화

```bash
# 메모리 사용량 모니터링
ragit monitor

# 프로세스 리소스 확인
ps aux | grep ragit

# 로그 크기 관리
du -sh logs/
```

## 🔬 프로그래밍 API

개발 중인 애플리케이션에서 RAGIT SDK를 직접 사용할 수 있습니다.

### 기본 사용법

```python
from ragit_sdk import RagitConfig, ProcessManager

# 설정 생성
config = RagitConfig()

# 프로세스 매니저 생성
process_manager = ProcessManager(config)

# 개발 모드로 서비스 시작
if process_manager.start_all(mode="dev"):
    print("✅ 개발 환경이 시작되었습니다!")

    # 서비스 상태 확인
    status = process_manager.get_status()
    print(f"실행 중인 서비스: {status}")
```

### 자동화 스크립트 예제

```python
#!/usr/bin/env python3
"""
개발 환경 자동 설정 스크립트
"""
from ragit_sdk import RagitConfig, ProcessManager
import time

def main():
    config = RagitConfig()
    config.log_level = "DEBUG"

    manager = ProcessManager(config)

    print("🚀 개발 환경을 시작합니다...")

    # 백엔드 먼저 시작
    manager.start_service("backend")
    time.sleep(5)

    # 게이트웨이 시작
    manager.start_service("gateway")
    time.sleep(3)

    # 프론트엔드 시작
    manager.start_service("frontend")

    print("✅ 모든 서비스가 실행되었습니다!")
    print("🌐 http://localhost:8000 에서 확인하세요")

if __name__ == "__main__":
    main()
```

### 유틸리티 함수 활용

```python
from ragit_sdk.utils import check_service_health, get_system_info

# 서비스 상태 확인
health = check_service_health("http://localhost:8001/health")
if health["status"] == "healthy":
    print(f"✅ 백엔드 응답 시간: {health['response_time_ms']}ms")

# 시스템 리소스 확인
system_info = get_system_info()
print(f"💾 메모리 사용률: {system_info['memory']['percent']}%")
print(f"🔥 CPU 사용률: {system_info['cpu_percent']}%")
```

---

## 📚 추가 리소스

### 문서 링크

- **📦 [설치 가이드](installation.md)**: Docker 기반 RAGIT 사용법
- **📖 [프로젝트 README](../README.md)**: 프로젝트 개요 및 구조
- **🔧 [문제 해결](#)**: 일반적인 문제 해결 방법

### 개발 참고자료

- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **NiceGUI 문서**: https://nicegui.io/
- **Celery 문서**: https://docs.celeryproject.org/
- **PostgreSQL 문서**: https://postgresql.org/docs/
- **Redis 문서**: https://redis.io/documentation

### 컨트리뷰션

RAGIT 프로젝트에 기여하고 싶다면:

1. **Fork & Clone**: 저장소를 포크하고 로컬에 클론
2. **개발 환경 설정**: 이 가이드를 따라 로컬 환경 구성
3. **브랜치 생성**: 기능별 브랜치에서 개발
4. **테스트 작성**: 새 기능에 대한 테스트 추가
5. **Pull Request**: 변경사항을 메인 저장소에 제출

---

💡 **일반 사용자이신가요?** Docker를 이용한 간단한 설치 및 사용법은 [설치 가이드](installation.md)를 참조하세요.