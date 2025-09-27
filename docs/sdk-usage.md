# RAGIT SDK 사용 가이드

RAGIT SDK는 모든 서비스를 통합 관리할 수 있는 강력한 도구입니다.

## 📋 목차

- [SDK 개요](#sdk-개요)
- [CLI 인터페이스](#cli-인터페이스)
- [프로세스 관리](#프로세스-관리)
- [Docker 관리](#docker-관리)
- [설정 관리](#설정-관리)
- [프로그래밍 API](#프로그래밍-api)
- [고급 사용법](#고급-사용법)

## 🚀 SDK 개요

RAGIT SDK는 다음 구성 요소로 이루어져 있습니다:

```
ragit_sdk/
├── cli.py              # 통합 CLI 인터페이스
├── config.py           # 설정 관리
├── process_manager.py  # 로컬 프로세스 관리
├── docker_manager.py   # Docker 컨테이너 관리
├── logger.py           # 로깅 시스템
└── utils.py           # 유틸리티 함수
```

### 주요 기능

- **통합 CLI**: 모든 기능을 `ragit` 명령어로 관리
- **프로세스 관리**: 로컬 서비스 시작/중지/모니터링
- **Docker 관리**: 컨테이너 기반 배포 및 관리
- **설정 관리**: 환경별 설정 자동 관리
- **로깅**: 색상 구분된 통합 로깅 시스템

## 🖥️ CLI 인터페이스

### 기본 명령어

```bash
# 도움말 보기
ragit --help

# 버전 확인
ragit --version

# 설정 정보 확인
ragit config
```

### 서비스 관리

```bash
# 모든 서비스 시작
ragit start

# 개발 모드로 시작
ragit start --mode dev

# 서비스 중지
ragit stop

# 서비스 재시작
ragit restart

# 서비스 상태 확인
ragit status

# 실시간 모니터링
ragit monitor
```

### Docker 관리

```bash
# Docker 이미지 빌드
ragit docker build --mode dev
ragit docker build --mode prod

# Docker 컨테이너 시작
ragit docker start --mode dev
ragit docker start --mode prod

# Docker 컨테이너 중지
ragit docker stop --mode dev

# Docker 컨테이너 상태 확인
ragit docker ps

# Docker 로그 확인
ragit docker logs                    # 모든 서비스 로그
ragit docker logs --service backend  # 특정 서비스 로그
ragit docker logs --no-follow        # 실시간 추적 비활성화
```

## 🔧 프로세스 관리

### 로컬 서비스 실행

RAGIT는 4개의 주요 서비스로 구성됩니다:

- **Backend**: FastAPI 기반 REST API 서버
- **Frontend**: NiceGUI 기반 웹 인터페이스
- **Gateway**: API 게이트웨이 및 프록시
- **RAG Worker**: Celery 기반 백그라운드 작업 처리

```bash
# 전체 시스템 시작
ragit start

# 개발 모드 (상세 로그 출력)
ragit start --mode dev

# 서비스 시작 순서 (자동):
# 1. Backend (8001)
# 2. Gateway (8080)
# 3. RAG Worker (백그라운드)
# 4. Frontend (8000)
```

### 개별 서비스 관리

```bash
# 프로세스 매니저 직접 사용
ragit-process start-backend
ragit-process start-frontend
ragit-process start-gateway
ragit-process start-rag-worker

ragit-process stop-backend
ragit-process restart-frontend
ragit-process status
```

### 모니터링

```bash
# 실시간 서비스 모니터링
ragit monitor

# 출력 예시:
# 📊 Service Status:
# ✅ BACKEND      RUNNING (port: 8001) (memory: 125.3MB) (pid: 12345)
# ✅ GATEWAY      RUNNING (port: 8080) (memory: 89.7MB) (pid: 12346)
# ✅ FRONTEND     RUNNING (port: 8000) (memory: 156.8MB) (pid: 12347)
# ✅ RAG_WORKER   RUNNING (memory: 98.4MB) (pid: 12348)
```

## 🐳 Docker 관리

### 환경 모드

RAGIT는 두 가지 Docker 환경을 지원합니다:

- **dev**: 개발 환경 (모든 서비스 단일 컨테이너)
- **prod**: 프로덕션 환경 (마이크로서비스 분리)

### 개발 환경 (dev)

```bash
# 개발 환경 빌드
ragit docker build --mode dev

# 개발 환경 시작
ragit docker start --mode dev

# 컨테이너 구성:
# - postgres (데이터베이스)
# - redis (캐시/큐)
# - ragit (모든 RAGIT 서비스)
```

### 프로덕션 환경 (prod)

```bash
# 프로덕션 환경 빌드
ragit docker build --mode prod

# 프로덕션 환경 시작
ragit docker start --mode prod

# 컨테이너 구성:
# - postgres (데이터베이스)
# - redis (캐시/큐)
# - backend (API 서버)
# - gateway (게이트웨이)
# - frontend (웹 UI)
# - rag-worker (백그라운드 워커)
```

### 로그 관리

```bash
# 모든 서비스 로그 (실시간)
ragit docker logs

# 특정 서비스 로그
ragit docker logs --service backend
ragit docker logs --service frontend

# 정적 로그 (실시간 추적 없음)
ragit docker logs --no-follow

# 기존 로그만 확인
ragit docker logs --service ragit --no-follow
```

## ⚙️ 설정 관리

### 환경 변수

RAGIT SDK는 환경 변수를 통해 설정을 관리합니다:

```bash
# 포트 설정
export FRONTEND_PORT=8000
export BACKEND_PORT=8001
export GATEWAY_PORT=8080

# 데이터베이스 설정
export DATABASE_URL=postgresql://postgres:password@localhost:5432/ragit
export REDIS_URL=redis://localhost:6379/0

# JWT 설정
export SECRET_KEY=your-secret-key
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 로깅 설정
export LOG_LEVEL=INFO
export RAGIT_ENV=development
```

### 설정 파일

**로컬 개발용 (.env):**
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/ragit
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
LOG_LEVEL=DEBUG
```

**Docker용 (.env.docker):**
```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragit
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

### 설정 확인

```bash
# 현재 설정 확인
ragit config

# 출력 예시:
# ⚙️ RAGIT 설정 정보:
# - 작업 디렉토리: /path/to/RAGIT
# - 로그 디렉토리: /path/to/RAGIT/logs
# - 데이터 디렉토리: /path/to/RAGIT/data
# - 환경: development
# - 서비스 포트:
#   - Frontend: 8000
#   - Backend: 8001
#   - Gateway: 8080
```

## 🔬 프로그래밍 API

SDK를 Python 코드에서 직접 사용할 수 있습니다:

### 기본 사용법

```python
from ragit_sdk import RagitConfig, ProcessManager, DockerManager

# 설정 생성
config = RagitConfig()

# 프로세스 매니저 생성
process_manager = ProcessManager(config)

# 모든 서비스 시작
if process_manager.start_all():
    print("✅ 모든 서비스가 시작되었습니다!")

    # 서비스 상태 확인
    process_manager.show_status()

    # 서비스 중지
    process_manager.stop_all()
```

### Docker 관리

```python
from ragit_sdk import DockerManager

# Docker 매니저 생성
docker_manager = DockerManager()

# 개발 환경 빌드 및 시작
if docker_manager.build("dev"):
    docker_manager.start("dev")

    # 컨테이너 상태 확인
    docker_manager.status("dev")

    # 로그 확인
    logs = docker_manager.get_service_logs("backend", lines=50)
    print(logs)
```

### 개별 서비스 관리

```python
# 개별 서비스 시작
process_manager.start_service("backend")
process_manager.start_service("frontend")

# 서비스 상태 확인
if process_manager.is_service_running("backend"):
    print("백엔드가 실행 중입니다")

# 서비스 재시작
process_manager.restart_service("gateway")
```

### 설정 커스터마이징

```python
from ragit_sdk import RagitConfig

# 커스텀 설정
config = RagitConfig()
config.frontend_port = 3000
config.backend_port = 3001
config.log_level = "DEBUG"

# 커스텀 설정으로 매니저 생성
process_manager = ProcessManager(config)
```

## 🎯 고급 사용법

### 서비스 헬스체크

```python
from ragit_sdk.utils import check_service_health

# 서비스 상태 확인
health = check_service_health("http://localhost:8001")
print(f"Status: {health['status']}")
print(f"Response time: {health['response_time_ms']}ms")
```

### 시스템 모니터링

```python
from ragit_sdk.utils import get_system_info

# 시스템 정보 확인
system_info = get_system_info()
print(f"CPU 사용률: {system_info['cpu_percent']}%")
print(f"메모리 사용률: {system_info['memory']['percent']}%")
```

### 로그 관리

```python
from ragit_sdk.logger import setup_logger, get_service_logger

# 로거 설정
logger = setup_logger("my_service", log_level="DEBUG")

# 서비스별 로거
service_logger = get_service_logger("backend")
service_logger.info("백엔드 서비스 시작")
```

### 포트 관리

```python
from ragit_sdk.utils import check_port_available, find_free_port

# 포트 사용 가능 여부 확인
if check_port_available(8000):
    print("포트 8000을 사용할 수 있습니다")

# 사용 가능한 포트 찾기
free_port = find_free_port(8000)
print(f"사용 가능한 포트: {free_port}")
```

## 🐛 디버깅

### 로그 레벨 설정

```bash
# 환경 변수로 설정
export LOG_LEVEL=DEBUG
ragit start

# 또는 .env 파일에 설정
echo "LOG_LEVEL=DEBUG" >> .env
```

### 상세 로그 확인

```bash
# 로그 파일 위치
ls -la logs/

# 실시간 로그 모니터링
tail -f logs/ragit_$(date +%Y%m%d).log

# 에러 로그만 확인
tail -f logs/ragit_error_$(date +%Y%m%d).log
```

### 문제 해결

```bash
# 서비스 상태 확인
ragit status

# 포트 충돌 확인
netstat -an | grep :8000

# 프로세스 정보 확인
ps aux | grep ragit

# Docker 컨테이너 상태 (Docker 사용 시)
ragit docker ps
```

## 📚 추가 리소스

- [설치 가이드](installation.md)
- [프로젝트 구조](../README.md)
- [API 문서](api-reference.md)
- [문제 해결](troubleshooting.md)