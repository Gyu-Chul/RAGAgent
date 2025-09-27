# RAGIT - RAG with Gateway-Backend Architecture

RAGIT은 Docker 기반의 자체 호스팅 RAG (Retrieval-Augmented Generation) 시스템입니다.

## 프로젝트 구조

```
RAGIT/
├── backend/         # Backend API 서버
├── frontend/        # Web UI (NiceGUI)
├── gateway/         # API Gateway
├── rag_worker/      # RAG 처리 워커
├── scripts/         # 관리 스크립트
├── pyproject.toml   # 통합 의존성 관리
├── Dockerfile       # Docker 이미지 빌드
├── docker-compose.yml # Docker 컨테이너 오케스트레이션
└── install.sh       # 자동 설치 스크립트
```

## 🚀 Quick Start

### SDK 기반 통합 CLI (권장)

RAGIT SDK를 사용하면 모든 기능을 하나의 명령어로 관리할 수 있습니다:

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 의존성 설치
uv sync

# 모든 서비스 시작
ragit start

# 개발 모드로 시작
ragit start --mode dev

# 서비스 상태 확인
ragit status

# 서비스 중지
ragit stop

# Docker 모드
ragit docker build --mode prod
ragit docker start --mode prod
ragit docker logs --service backend
```

### 자동 설치 (Docker)
```bash
# 자동 설치 스크립트 실행
chmod +x install.sh
./install.sh
```

설치 스크립트가 다음을 자동으로 처리합니다:
- Docker 환경 확인
- Docker 이미지 빌드
- 컨테이너 시작
- 서비스 상태 확인

### 2. 수동 Docker 설치
```bash
# Docker 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 🎯 접속 정보

설치 완료 후 다음 주소로 접속:

- **웹 인터페이스**: http://localhost:8000
- **백엔드 API**: http://localhost:8001
- **게이트웨이**: http://localhost:8080

## 📋 RAGIT CLI 사용법

### 기본 명령어
```bash
# 서비스 관리
ragit start           # 모든 서비스 시작
ragit stop            # 모든 서비스 중지
ragit restart         # 모든 서비스 재시작
ragit status          # 서비스 상태 확인
ragit monitor         # 실시간 모니터링
ragit config          # 설정 정보 표시

# 개발 모드
ragit start --mode dev    # 개발 모드로 시작
```

### Docker 관리
```bash
# Docker 이미지 빌드
ragit docker build --mode dev
ragit docker build --mode prod

# Docker 컨테이너 관리
ragit docker start --mode dev
ragit docker stop --mode dev
ragit docker restart --mode dev
ragit docker ps

# Docker 로그 확인
ragit docker logs                    # 모든 서비스 로그
ragit docker logs --service backend  # 특정 서비스 로그
ragit docker logs --no-follow        # 실시간 추적 비활성화
```

### 레거시 Docker 명령어 (호환성)
```bash
# 서비스 시작/중지
docker-compose up -d
docker-compose down

# 로그 확인
docker-compose logs -f
```

## 🛠️ 개발 환경 (로컬 실행)

개발 목적으로 Docker 없이 실행하려면:

### 1. 사전 요구사항
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 2. 의존성 설치
```bash
# UV 사용 (권장)
uv sync --dev

# 또는 pip 사용
pip install -e .
pip install -r requirements.txt
```

### 3. 환경 설정
```bash
# .env 파일 생성
cp .env.example .env
# 데이터베이스 정보 수정
```

### 4. 개발 서버 실행
```bash
# 개별 서비스 실행
uv run dev-backend     # 백엔드만
uv run dev-frontend    # 프론트엔드만
uv run dev-gateway     # 게이트웨이만
uv run dev-rag-worker  # RAG 워커만

# 또는 통합 실행
python start.py
```

## 🔧 개발 도구

```bash
# 코드 포맷팅
uv run black .
uv run isort .

# 린팅
uv run flake8 .

# 테스트
uv run pytest
```

## 📊 모니터링

### Docker 환경
```bash
# 컨테이너 리소스 사용량
docker stats

# 서비스 헬스체크
docker-compose exec ragit curl http://localhost:8001/health
```

### 로그 위치
- **Docker**: `docker-compose logs`
- **로컬**: `./logs/` 디렉토리


### 디버깅 모드
```bash
# 디버그 로그와 함께 실행
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```
