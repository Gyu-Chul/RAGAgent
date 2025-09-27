# RAGIT


## 프로젝트 구조

```
RAGIT/
├── backend/         # Backend API 서버
├── frontend/        # Web UI (NiceGUI)
├── gateway/         # API Gateway
├── rag_worker/      # RAG 처리 워커
├── scripts/         # 프로세스 관리 스크립트
├── pyproject.toml   # 통합 의존성 관리
├── start.py         # 전체 시스템 시작
└── stop.py          # 전체 시스템 종료
```

## 설치 및 실행

### 1. 의존성 설치

UV 사용 (권장):
```bash
uv sync
```

Poetry 사용:
```bash
poetry install
```

### 2. 시스템 실행

**전체 시스템 한 번에 실행:**
```bash
python start.py
```

**개별 서비스 실행:**
```bash
# 백엔드만
uv run backend

# 프론트엔드만
uv run frontend

# 게이트웨이만
uv run gateway

# RAG 워커만
uv run rag-worker
```

**프로세스 매니저 직접 사용:**
```bash
# 모든 서비스 시작
python -m scripts.process_manager start-all

# 서비스 상태 확인
python -m scripts.process_manager status

# 서비스 모니터링
python -m scripts.process_manager monitor

# 모든 서비스 종료
python -m scripts.process_manager stop-all
```

### 3. 시스템 종료

```bash
python stop.py
```

또는 실행 중인 터미널에서 `Ctrl+C`

## 서비스 정보

- **Frontend**: http://localhost:8000 - 웹 인터페이스
- **Backend**: http://localhost:8001 - 백엔드 API
- **Gateway**: http://localhost:8080 - API 게이트웨이
- **RAG Worker**: 백그라운드 처리 워커 (Celery)

## 사전 요구사항

1. **Redis 실행:**
```bash
docker run --name my-redis -p 6379:6379 -d redis
```

2. **Python 3.11 이상**

## 개발

```bash
# 개발 의존성 설치
uv sync --dev

# 코드 포맷팅
uv run black .
uv run isort .

# 린팅
uv run flake8 .
```

## 주의사항

- Celery는 Windows에서 제약이 있어 solo 모드로 실행됩니다
- 모든 서비스는 프로세스 매니저를 통해 통합 관리됩니다
- 개별 모듈의 requirements.txt는 제거되고 루트의 pyproject.toml로 통합 관리됩니다