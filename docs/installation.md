# RAGIT 설치 가이드

RAGIT을 설치하고 실행하는 다양한 방법을 설명합니다.

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [Docker 설치 (권장)](#docker-설치-권장)
- [로컬 개발 환경 설치](#로컬-개발-환경-설치)
- [환경 설정](#환경-설정)
- [설치 확인](#설치-확인)

## 🖥️ 시스템 요구사항

### 공통 요구사항
- **운영체제**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **메모리**: 최소 4GB RAM (권장 8GB+)
- **디스크**: 최소 2GB 여유 공간

### Docker 설치 시
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 로컬 개발 환경 설치 시
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+

## 🐳 Docker 설치 (권장)

Docker를 사용한 설치가 가장 간단하고 안정적입니다.

### 1. 사전 준비

#### Docker 설치
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# macOS (Homebrew)
brew install --cask docker

# Windows
# Docker Desktop 다운로드: https://docker.com/products/docker-desktop
```

#### Docker Compose 설치
```bash
# Linux
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# macOS/Windows
# Docker Desktop에 포함됨
```

### 2. 자동 설치 (가장 간단)

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 자동 설치 스크립트 실행
chmod +x install.sh
./install.sh
```

자동 설치 스크립트가 다음을 처리합니다:
- Docker 환경 확인
- 환경 설정 파일 생성
- Docker 이미지 빌드
- 컨테이너 시작
- 서비스 상태 확인

### 3. 수동 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 환경 설정 파일 생성
cp .env.example .env.docker
# .env.docker 파일 수정 (필요시)

# Docker 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 💻 로컬 개발 환경 설치

개발 목적이나 Docker를 사용할 수 없는 환경에서의 설치 방법입니다.

### 1. 사전 준비

#### Python 설치
```bash
# Python 3.11+ 설치 확인
python3 --version

# UV 패키지 매니저 설치 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 데이터베이스 설치

**PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Windows
# PostgreSQL 다운로드: https://postgresql.org/download/windows/
```

**Redis:**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
brew services start redis

# Windows
# Redis 다운로드: https://github.com/tporadowski/redis/releases
```

### 2. RAGIT 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 의존성 설치 (UV 사용)
uv sync --dev

# 또는 pip 사용
pip install -e .
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
sudo -u postgres createdb ragit

# 사용자 생성 (선택사항)
sudo -u postgres createuser --interactive
```

## ⚙️ 환경 설정

### Docker 환경 설정

`.env.docker` 파일을 생성하거나 수정:

```bash
# Database Configuration (Docker internal network)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragit

# Redis Configuration (Docker internal network)
REDIS_URL=redis://redis:6379/0

# JWT Configuration
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=["http://localhost:8000"]
```

### 로컬 개발 환경 설정

`.env` 파일을 생성:

```bash
# Database Configuration (Local)
DATABASE_URL=postgresql://postgres:password@localhost:5432/ragit

# Redis Configuration (Local)
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=["http://localhost:8000"]

# Service Ports
FRONTEND_PORT=8000
BACKEND_PORT=8001
GATEWAY_PORT=8080

# Logging
LOG_LEVEL=INFO
```

## ✅ 설치 확인

### Docker 환경

```bash
# 컨테이너 상태 확인
docker-compose ps

# 서비스 접속 테스트
curl http://localhost:8001/health
curl http://localhost:8080/health
```

### 로컬 환경

```bash
# RAGIT CLI 설치 확인
ragit --version

# 설정 확인
ragit config

# 서비스 시작
ragit start --mode dev

# 서비스 상태 확인
ragit status
```

### 웹 인터페이스 접속

설치가 완료되면 다음 주소로 접속할 수 있습니다:

- **웹 인터페이스**: http://localhost:8000
- **백엔드 API**: http://localhost:8001
- **API 게이트웨이**: http://localhost:8080

## 🔧 문제 해결

### 일반적인 문제

**포트 충돌:**
```bash
# 사용 중인 포트 확인
netstat -an | grep :8000

# 프로세스 종료
sudo kill -9 $(lsof -ti:8000)
```

**Docker 권한 문제 (Linux):**
```bash
# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 로그아웃 후 다시 로그인
```

**데이터베이스 연결 실패:**
```bash
# PostgreSQL 서비스 확인
sudo systemctl status postgresql

# Redis 서비스 확인
sudo systemctl status redis
```

### 로그 확인

**Docker 환경:**
```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f ragit
```

**로컬 환경:**
```bash
# RAGIT 로그 디렉토리
ls -la logs/

# 실시간 모니터링
ragit monitor
```

## 🆘 지원

문제가 지속되거나 추가 도움이 필요한 경우:

- **GitHub Issues**: https://github.com/your-repo/RAGIT/issues
- **문서**: docs/ 디렉토리의 다른 가이드 참조
- **커뮤니티**: 프로젝트 토론 섹션 활용