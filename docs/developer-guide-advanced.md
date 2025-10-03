# RAGIT 고급 개발자 가이드

각 서비스를 개별적으로 실행하여 세밀한 개발 및 디버깅을 수행하는 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [사전 준비](#사전-준비)
- [인프라 실행](#인프라-실행)
- [서비스 개별 실행](#서비스-개별-실행)
- [환경변수 설정](#환경변수-설정)
- [실행 순서](#실행-순서)
- [문제 해결](#문제-해결)

## 🎯 개요

RAGIT은 기본적으로 통합 명령어(`ragit start`)로 모든 서비스를 자동 실행합니다.
하지만 개발 및 디버깅을 위해 각 서비스를 개별적으로 실행할 수 있습니다.

### 언제 개별 서비스 실행을 사용하나요?

- ✅ 특정 서비스만 디버깅하고 싶을 때
- ✅ 서비스별로 다른 환경변수를 테스트할 때
- ✅ IDE에서 직접 디버거를 연결하고 싶을 때
- ✅ 서비스 간 통신 문제를 진단할 때
- ✅ 로그를 개별적으로 확인하고 싶을 때

## 🔧 사전 준비

### 1. Python 환경 설정

```bash
# Python 3.11+ 필요
python --version

# UV 패키지 매니저 설치 (권장)
pip install uv
```

### 2. 의존성 설치

```bash
# 프로젝트 루트 디렉토리에서
uv sync
```

### 3. Docker 설치 확인

인프라(PostgreSQL, Redis)는 Docker로 실행됩니다.

```bash
# Docker 설치 확인
docker --version
docker-compose --version
```

## 🐳 인프라 실행

먼저 PostgreSQL과 Redis를 Docker로 실행합니다.

### 방법 1: RAGIT CLI 사용 (권장)

```bash
ragit infra
```

출력 예시:
```
Starting local infrastructure (PostgreSQL, Redis)...
Local infrastructure started successfully!
PostgreSQL: localhost:5432
Redis: localhost:6379
```

### 방법 2: Docker Compose 직접 사용

```bash
docker-compose -f docker-compose.local.yml up -d
```

### 인프라 상태 확인

```bash
# 컨테이너 상태 확인
docker ps | grep ragit

# PostgreSQL 연결 테스트
docker exec -it ragit-postgres psql -U postgres -d ragit -c "SELECT 1;"

# Redis 연결 테스트
docker exec -it ragit-redis redis-cli ping
```

## 🚀 서비스 개별 실행

각 서비스를 별도의 터미널 창에서 실행하세요.

### 1. Backend (포트: 8001)

```bash
# 터미널 1
uv run python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

**확인:**
```bash
curl http://localhost:8001/health
# {"status":"healthy","message":"Backend server is running"}
```

### 2. Gateway (포트: 8080)

```bash
# 터미널 2
uv run python -m gateway.main
```

**Gateway의 main.py를 확인하여 uvicorn 실행 방식 확인:**
```bash
# gateway/main.py에 uvicorn 실행 코드가 있다면
uv run python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8080
```

**확인:**
```bash
curl http://localhost:8080/
# {"message":"RAG Agent Gateway","version":"1.0.0"}
```

### 3. RAG Worker (Celery)

**Windows:**
```bash
# 터미널 3
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info --pool=solo
```

**Linux/Mac:**
```bash
# 터미널 3
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info
```

**확인:**
```bash
# Celery 프로세스 확인
ps aux | grep celery  # Linux/Mac
tasklist | findstr python  # Windows
```

### 4. Frontend (포트: 8000)

```bash
# 터미널 4
uv run python -m frontend.main
```

**확인:**
- 브라우저에서 http://localhost:8000 접속

## ⚙️ 환경변수 설정

각 서비스 실행 시 필요한 환경변수를 설정합니다.

### 공통 환경변수

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ragit"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key-here"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="1440"
```

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ragit"
$env:REDIS_URL="redis://localhost:6379/0"
$env:SECRET_KEY="your-secret-key-here"
```

**Windows (CMD):**
```cmd
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragit
set REDIS_URL=redis://localhost:6379/0
set SECRET_KEY=your-secret-key-here
```

### Frontend 추가 환경변수

```bash
export GATEWAY_URL="http://localhost:8080"
export BACKEND_URL="http://localhost:8001"
```

### Gateway 추가 환경변수

```bash
export BACKEND_URL="http://localhost:8001"
export CORS_ORIGINS='["http://localhost:8000"]'
```

### .env 파일 사용 (권장)

프로젝트 루트에 `.env` 파일을 생성:

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragit
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Service URLs
GATEWAY_URL=http://localhost:8080
BACKEND_URL=http://localhost:8001
CORS_ORIGINS=["http://localhost:8000"]

# Ports
FRONTEND_PORT=8000
BACKEND_PORT=8001
GATEWAY_PORT=8080

# Logging
LOG_LEVEL=INFO
```

## 📝 실행 순서

서비스는 다음 순서대로 실행하는 것을 권장합니다:

### 1단계: 인프라 시작
```bash
ragit infra
# 또는
docker-compose -f docker-compose.local.yml up -d
```

⏳ **대기:** PostgreSQL과 Redis가 완전히 시작될 때까지 약 5-10초 대기

### 2단계: Backend 시작
```bash
# 터미널 1
uv run python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

⏳ **대기:** Backend가 DB 연결을 완료할 때까지 약 2-3초 대기

### 3단계: Gateway 시작
```bash
# 터미널 2
uv run python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8080
```

⏳ **대기:** Gateway가 시작될 때까지 약 2초 대기

### 4단계: RAG Worker 시작
```bash
# 터미널 3 (Windows)
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info --pool=solo

# 터미널 3 (Linux/Mac)
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info
```

⏳ **대기:** Celery worker가 시작될 때까지 약 2-3초 대기

### 5단계: Frontend 시작
```bash
# 터미널 4
uv run python -m frontend.main
```

⏳ **대기:** Frontend가 시작될 때까지 약 2-3초 대기

### 6단계: 확인
브라우저에서 http://localhost:8000 접속하여 정상 동작 확인

## 🔍 문제 해결

### 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인 (Linux/Mac)
lsof -i :8000
lsof -i :8001
lsof -i :8080

# 포트 사용 중인 프로세스 확인 (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :8001
netstat -ano | findstr :8080

# 프로세스 종료
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 로그 확인
docker logs ragit-postgres

# PostgreSQL 재시작
docker restart ragit-postgres

# 연결 테스트
psql postgresql://postgres:postgres@localhost:5432/ragit -c "SELECT 1;"
```

### Redis 연결 실패

```bash
# Redis 컨테이너 로그 확인
docker logs ragit-redis

# Redis 재시작
docker restart ragit-redis

# 연결 테스트
redis-cli -h localhost -p 6379 ping
```

### Celery Worker 시작 실패

**Windows에서 "pool solo" 누락 오류:**
```bash
# Windows에서는 반드시 --pool=solo 옵션 사용
uv run python -m celery -A rag_worker.celery_app worker --loglevel=info --pool=solo
```

**Redis 연결 오류:**
```bash
# REDIS_URL 환경변수 확인
echo $REDIS_URL  # Linux/Mac
echo %REDIS_URL%  # Windows CMD
$env:REDIS_URL   # Windows PowerShell
```

### Frontend 시작 실패

**Import 에러:**
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/frontend"  # Linux/Mac
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)\frontend"  # Windows PowerShell
```

**Gateway 연결 실패:**
```bash
# Gateway URL 확인
curl http://localhost:8080/

# GATEWAY_URL 환경변수 확인
echo $GATEWAY_URL
```

### 로그 확인

각 서비스의 로그는 `logs/YYYY-MM-DD/` 디렉토리에 저장됩니다:

```bash
# 최신 로그 확인
ls -lt logs/$(date +%Y-%m-%d)/

# 특정 서비스 로그 tail
tail -f logs/$(date +%Y-%m-%d)/backend_*.log
tail -f logs/$(date +%Y-%m-%d)/gateway_*.log
tail -f logs/$(date +%Y-%m-%d)/frontend_*.log
```

## 🛑 서비스 종료

### 개별 서비스 종료
각 터미널에서 `Ctrl+C`를 눌러 서비스를 종료합니다.

### 인프라 종료
```bash
# Docker 인프라 종료
docker-compose -f docker-compose.local.yml down

# 데이터까지 삭제하려면
docker-compose -f docker-compose.local.yml down -v
```

### 전체 종료 스크립트 (선택사항)

**Linux/Mac:**
```bash
#!/bin/bash
# stop-all.sh

# 서비스 프로세스 종료
pkill -f "uvicorn backend.main"
pkill -f "uvicorn gateway.main"
pkill -f "frontend.main"
pkill -f "celery.*rag_worker"

# Docker 인프라 종료
docker-compose -f docker-compose.local.yml down

echo "All services stopped"
```

**Windows (PowerShell):**
```powershell
# stop-all.ps1

# 서비스 프로세스 종료
Get-Process | Where-Object {$_.CommandLine -like "*uvicorn backend.main*"} | Stop-Process
Get-Process | Where-Object {$_.CommandLine -like "*uvicorn gateway.main*"} | Stop-Process
Get-Process | Where-Object {$_.CommandLine -like "*frontend.main*"} | Stop-Process
Get-Process | Where-Object {$_.CommandLine -like "*celery*rag_worker*"} | Stop-Process

# Docker 인프라 종료
docker-compose -f docker-compose.local.yml down

Write-Host "All services stopped"
```

## 💡 팁

### 개발 워크플로우

1. **인프라는 항상 실행 상태 유지**
   ```bash
   ragit infra  # 한 번만 실행하고 계속 사용
   ```

2. **수정 중인 서비스만 재시작**
   - Backend 코드 수정 → Backend만 재시작
   - Frontend UI 수정 → Frontend만 재시작

3. **IDE 디버거 연결**
   - VSCode, PyCharm 등에서 각 서비스의 main.py를 직접 디버깅 모드로 실행

4. **로그 모니터링**
   ```bash
   # 별도 터미널에서 실시간 로그 확인
   ragit monitor  # 전체 시스템 모니터링

   # 또는 개별 로그 tail
   tail -f logs/$(date +%Y-%m-%d)/*.log
   ```

## 📞 지원

문제가 지속되거나 추가 도움이 필요한 경우:

- **GitHub Issues**: https://github.com/your-repo/RAGIT/issues
- **통합 실행 가이드**: [설치 가이드](installation.md)
- **SDK 사용법**: [SDK 가이드](sdk-usage.md)

---

💡 **일반 개발은?** 기본 개발 환경 설정은 [개발자 가이드](sdk-usage.md)를, 프로덕션 배포는 [설치 가이드](installation.md)를 참조하세요.
