# RAGIT SDK - 시스템 관리 도구

## 목차
- [개요](#개요)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [CLI 명령어](#cli-명령어)
- [사용 시나리오](#사용-시나리오)
- [프로젝트 구조](#프로젝트-구조)

---

## 개요

RAGIT SDK는 RAGIT 시스템 전체를 관리하는 **통합 CLI 도구**입니다.

### 주요 기능
- 🚀 **전체 시스템 시작/중지** - 한 번의 명령으로 모든 서비스 제어
- 🐳 **Docker 인프라 관리** - PostgreSQL, Redis, Milvus 자동 관리
- 📊 **실시간 모니터링** - 서비스 상태 및 로그 확인
- 🧪 **테스트 실행** - 통합 테스트 및 검증

---

## 설치

```bash
# ragit_sdk 폴더에서 설치
pip install -e .

# 설치 확인
ragit --version
```

---

## 빠른 시작

### 전체 시스템 시작

```bash
# 1. 인프라 + 모든 서비스 시작
ragit start

# 시작 순서:
# - Docker Infrastructure (PostgreSQL, Redis, Milvus)
# - Backend (Port 9090)
# - Gateway (Port 8080)
# - RAG Worker (Celery)
# - Frontend (Port 8000)
```

**시작 완료 화면**:
```
🚀 Starting RAGIT system...
🐳 Starting local infrastructure (PostgreSQL, Redis, Milvus)
✅ Local infrastructure started successfully
⏳ Waiting for services to be healthy...
✅ All services are healthy

🚀 Starting backend on port 9090...
✅ backend is ready at http://localhost:9090

🚀 Starting gateway on port 8080...
✅ gateway is ready at http://localhost:8080

🚀 Starting rag_worker...
✅ rag_worker is ready

🚀 Starting frontend on port 8000...
✅ frontend is ready at http://localhost:8000

✅ All services started successfully!

🌐 Service URLs:
   Frontend:  http://localhost:8000
   Backend:   http://localhost:9090
   Gateway:   http://localhost:8080
```

### 상태 확인

```bash
ragit status
```

**출력 예시**:
```
📊 Service Status:

🐳 Docker Infrastructure:
✅ POSTGRESQL   RUNNING (port: 5432) [healthy]
✅ REDIS        RUNNING (port: 6379) [healthy]

🚀 RAGIT Services:
✅ BACKEND      RUNNING (port: 9090) (memory: 125.3MB) (pid: 12345)
✅ GATEWAY      RUNNING (port: 8080) (memory: 89.1MB) (pid: 12346)
✅ RAG_WORKER   RUNNING (memory: 201.5MB) (pid: 12347)
✅ FRONTEND     RUNNING (port: 8000) (memory: 156.8MB) (pid: 12348)
```

### 시스템 종료

```bash
ragit stop
```

**종료 순서**:
1. Frontend
2. RAG Worker
3. Gateway
4. Backend
5. Docker Infrastructure (PostgreSQL, Redis, Milvus)

---

## CLI 명령어

### 시스템 관리

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ragit start` | 전체 시스템 시작 | `ragit start` |
| `ragit start --mode dev` | 개발 모드로 시작 | `ragit start --mode dev` |
| `ragit stop` | 전체 시스템 종료 | `ragit stop` |
| `ragit restart` | 전체 시스템 재시작 | `ragit restart` |
| `ragit status` | 시스템 상태 확인 | `ragit status` |
| `ragit monitor` | 실시간 모니터링 | `ragit monitor` |
| `ragit config` | 설정 정보 확인 | `ragit config` |

### 인프라 관리

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ragit infra` | 인프라만 시작 (PostgreSQL, Redis, Milvus) | `ragit infra` |

**인프라만 시작하는 경우**:
- Backend/Frontend 개발 시 인프라만 필요할 때
- 로컬에서 직접 서비스를 실행하고 싶을 때

### Docker 관리

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ragit docker build` | Docker 이미지 빌드 | `ragit docker build --mode dev` |
| `ragit docker start` | Docker 컨테이너 시작 | `ragit docker start` |
| `ragit docker stop` | Docker 컨테이너 종료 | `ragit docker stop` |
| `ragit docker ps` | 컨테이너 상태 확인 | `ragit docker ps` |
| `ragit docker logs` | 컨테이너 로그 확인 | `ragit docker logs --service backend` |

### 테스트 실행

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ragit test worker` | Git Worker 통합 테스트 | `ragit test worker` |
| `ragit test search` | 검색 기능 테스트 | `ragit test search` |
| `ragit test milvus` | Milvus 데이터 확인 | `ragit test milvus` |

---

## 사용 시나리오

### 시나리오 1: 로컬 개발 환경 구축

```bash
# 1. 전체 시스템 시작
ragit start

# 2. Frontend 접속
# http://localhost:8000

# 3. 개발 완료 후 종료
ragit stop
```

### 시나리오 2: Backend만 개발하는 경우

```bash
# 1. 인프라만 시작
ragit infra

# 2. Backend 직접 실행 (별도 터미널)
cd backend
python main.py

# 3. Gateway 직접 실행 (별도 터미널)
cd gateway
python main.py

# 4. 테스트
curl http://localhost:9090/health
```

### 시나리오 3: 서비스 모니터링

```bash
# 실시간 모니터링 시작
ragit monitor
```

**모니터링 화면**:
```
👀 Starting service monitoring (Ctrl+C to stop)
📋 Real-time log monitoring and health check...

📄 Monitoring backend log: logs/2025-01-18/backend_10-30-45.log
📄 Monitoring frontend log: logs/2025-01-18/frontend_10-30-46.log
📄 Monitoring gateway log: logs/2025-01-18/gateway_10-30-44.log
📄 Monitoring rag_worker log: logs/2025-01-18/rag_worker_10-30-47.log

📈 Real-time log streaming started...
💡 Health checks every 30 seconds, logs are streamed in real-time

[backend] 2025-01-18 10:31:00 - INFO - Application startup complete
[frontend] 2025-01-18 10:31:02 - INFO - Server started at http://0.0.0.0:8000
...

================================================================================
📊 Health Check Update:
   ✅ BACKEND      RUNNING  Port:9090 🟢 (15ms)
   ✅ GATEWAY      RUNNING  Port:8080 🟢 (12ms)
   ✅ RAG_WORKER   RUNNING
   ✅ FRONTEND     RUNNING  Port:8000 🟢 (18ms)
================================================================================
```

### 시나리오 4: 시스템 재시작

```bash
# 전체 시스템 재시작
ragit restart

# 특정 서비스만 재시작할 수 없음 (전체만 가능)
```

### 시나리오 5: Docker로 배포

```bash
# 1. Docker 이미지 빌드 (프로덕션 모드)
ragit docker build --mode prod

# 2. Docker 컨테이너 시작
ragit docker start --mode prod

# 3. 상태 확인
ragit docker ps

# 4. 로그 확인
ragit docker logs --service backend --follow
```

---

## 프로젝트 구조

```
ragit_sdk/
│
├── cli.py                  # CLI 진입점 (ragit 명령어)
├── config.py               # 설정 관리 (포트, 경로 등)
├── logger.py               # 로깅 시스템
│
├── core/                   # 핵심 기능
│   ├── process_manager.py # 프로세스 관리
│   └── docker_manager.py  # Docker 관리
│
└── tests/                  # 테스트 스크립트
    ├── test_git_worker.py # Git Worker 테스트
    ├── test_search_only.py # 검색 테스트
    └── check_milvus.py    # Milvus 데이터 확인
```

### 주요 모듈 설명

#### 1. ProcessManager (core/process_manager.py)

**역할**: 모든 서비스의 프로세스 생명주기 관리

**주요 클래스**:
- `ProcessMonitor`: 프로세스 출력 모니터링
- `ServiceController`: 개별 서비스 시작/중지
- `SystemOrchestrator`: 전체 시스템 오케스트레이션
- `ProcessManager`: 통합 관리 인터페이스

**시작 순서**:
1. Docker Infrastructure (PostgreSQL, Redis, Milvus)
2. Backend (Port 9090)
3. Gateway (Port 8080)
4. RAG Worker (Celery)
5. Frontend (Port 8000)

**종료 순서**:
1. Frontend
2. RAG Worker
3. Gateway
4. Backend
5. Docker Infrastructure

#### 2. DockerManager (core/docker_manager.py)

**역할**: Docker 컨테이너 관리

**주요 기능**:
- `start_local_infrastructure()`: PostgreSQL, Redis, Milvus 시작
- `stop_local_infrastructure()`: 인프라 종료
- `build()`: Docker 이미지 빌드
- `logs()`: 컨테이너 로그 확인

**Docker Compose 파일**:
- `docker-compose.local.yml`: 로컬 인프라 (PostgreSQL, Redis, Milvus)
- `docker-compose.dev.yml`: 개발 환경
- `docker-compose.prod.yml`: 프로덕션 환경

#### 3. RagitConfig (config.py)

**역할**: 환경 설정 관리

**설정 항목**:
```python
frontend_port = 8000
backend_port = 9090
gateway_port = 8080

work_dir = Path.cwd()
log_dir = work_dir / "logs"
data_dir = work_dir / "data"
```

---

## 설정 정보 확인

```bash
ragit config
```

**출력 예시**:
```
RAGIT configuration:
- Work directory: C:\Users\su9ki\Desktop\RAGIT
- Log directory: C:\Users\su9ki\Desktop\RAGIT\logs
- Data directory: C:\Users\su9ki\Desktop\RAGIT\data
- Environment: development
- Service ports:
  - Frontend: 8000
  - Backend: 9090
  - Gateway: 8080
```

---

## 로그 확인

### 로그 파일 위치

```
logs/
└── {YYYY-MM-DD}/
    ├── backend_{HH-MM-SS}.log
    ├── frontend_{HH-MM-SS}.log
    ├── gateway_{HH-MM-SS}.log
    └── rag_worker_{HH-MM-SS}.log
```

### 로그 확인 방법

```bash
# 1. 실시간 모니터링
ragit monitor

# 2. Docker 로그 (Docker 모드인 경우)
ragit docker logs --service backend --follow

# 3. 직접 파일 확인
cat logs/2025-01-18/backend_10-30-45.log
```

---

## 문제 해결

### 1. 포트 충돌

```
문제: 포트가 이미 사용 중입니다
해결:
  1. 실행 중인 서비스 확인: ragit status
  2. 종료: ragit stop
  3. 포트 확인: netstat -ano | findstr "8000"
```

### 2. Docker 연결 실패

```
문제: Docker daemon is not running
해결:
  1. Docker Desktop 실행 확인
  2. Docker 상태 확인: docker info
```

### 3. 서비스 시작 실패

```
문제: 일부 서비스가 시작되지 않음
해결:
  1. 상태 확인: ragit status
  2. 로그 확인: ragit monitor
  3. 재시작: ragit restart
```

---

## 개발 모드 vs 프로덕션 모드

| 항목 | 개발 모드 (dev) | 프로덕션 모드 (prod) |
|------|----------------|-------------------|
| **실행 방식** | 로컬 프로세스 | Docker 컨테이너 |
| **로그** | 파일 + 콘솔 | 파일 |
| **재시작** | 자동 (코드 변경 시) | 수동 |
| **디버깅** | 가능 | 제한적 |
| **용도** | 로컬 개발 | 배포 |

**개발 모드 시작**:
```bash
ragit start --mode dev
```

**프로덕션 모드 시작**:
```bash
ragit docker build --mode prod
ragit docker start --mode prod
```

---

## 요약

```bash
# 개발 시작
ragit start

# 상태 확인
ragit status

# 모니터링
ragit monitor

# 종료
ragit stop
```

**모든 명령어는 프로젝트 루트에서 실행하세요!**
