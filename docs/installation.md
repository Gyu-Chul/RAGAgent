# RAGIT 설치 및 사용 가이드

RAGIT을 Docker를 통해 설치하고 사용하는 방법을 설명합니다.

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [빠른 시작](#빠른-시작)
- [상세 설치 과정](#상세-설치-과정)
- [환경 설정](#환경-설정)
- [서비스 관리](#서비스-관리)
- [문제 해결](#문제-해결)

## 🖥️ 시스템 요구사항

- **운영체제**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **메모리**: 최소 4GB RAM (권장 8GB+)
- **디스크**: 최소 3GB 여유 공간
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 🚀 빠른 시작

가장 빠르게 RAGIT을 실행하는 방법입니다.

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# 2. Docker로 실행
docker-compose up -d

# 3. 서비스 확인
docker-compose ps
```

웹 브라우저에서 http://localhost:8000 으로 접속하면 RAGIT 인터페이스를 사용할 수 있습니다.

## 📦 상세 설치 과정

### 1. Docker 설치

Docker가 설치되어 있지 않다면 먼저 설치하세요.

#### Ubuntu/Debian
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# 로그아웃 후 다시 로그인
```

#### macOS
```bash
# Homebrew로 설치
brew install --cask docker

# 또는 Docker Desktop 다운로드
# https://docker.com/products/docker-desktop
```

#### Windows
Docker Desktop을 다운로드하여 설치하세요: https://docker.com/products/docker-desktop

### 2. RAGIT 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/RAGIT.git
cd RAGIT

# Docker 이미지 빌드
docker-compose build

# 서비스 시작 (백그라운드)
docker-compose up -d
```

### 3. 서비스 확인

```bash
# 모든 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f frontend
docker-compose logs -f backend
```

## ⚙️ 환경 설정

기본 설정으로도 충분히 사용할 수 있지만, 필요에 따라 설정을 변경할 수 있습니다.

### 환경 변수 설정

`.env` 파일을 생성하여 설정을 변경할 수 있습니다:

```bash
# JWT 보안 키 (프로덕션에서는 반드시 변경)
SECRET_KEY=your-super-secret-key-here

# 데이터베이스 설정 (기본값 사용 권장)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragit
REDIS_URL=redis://redis:6379/0

# 서비스 포트 (기본값)
FRONTEND_PORT=8000
BACKEND_PORT=8001
GATEWAY_PORT=8080

# 로그 레벨
LOG_LEVEL=INFO
```

### 포트 변경

기본 포트가 사용 중인 경우 `docker-compose.yml`에서 포트를 변경할 수 있습니다:

```yaml
services:
  frontend:
    ports:
      - "3000:8000"  # 외부 포트를 3000으로 변경

  backend:
    ports:
      - "3001:8001"  # 외부 포트를 3001로 변경
```

## 🎯 서비스 관리

### 기본 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart frontend

# 서비스 상태 확인
docker-compose ps
```

### 로그 확인

```bash
# 모든 서비스 로그 (실시간)
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f gateway
docker-compose logs -f rag-worker

# 최근 로그만 확인 (실시간 추적 없음)
docker-compose logs --tail=100
```

### 웹 인터페이스 접속

설치가 완료되면 다음 주소로 접속할 수 있습니다:

- **📱 웹 인터페이스**: http://localhost:8000
- **🔌 백엔드 API**: http://localhost:8001
- **🌉 API 게이트웨이**: http://localhost:8080

### 서비스 상태 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 서비스 헬스체크
curl http://localhost:8001/health
curl http://localhost:8080/

# 자세한 시스템 정보
docker-compose top
```

## 🔧 문제 해결

### 일반적인 문제

#### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | grep :8000
# 또는
lsof -i :8000

# Docker 컨테이너 중지 후 재시작
docker-compose down
docker-compose up -d
```

#### Docker 권한 문제 (Linux)
```bash
# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 로그아웃 후 다시 로그인
# 또는 새 세션에서 실행
newgrp docker
```

#### 컨테이너가 시작되지 않는 경우
```bash
# 컨테이너 상태 확인
docker-compose ps

# 문제가 있는 서비스 로그 확인
docker-compose logs [service-name]

# 이미지 다시 빌드
docker-compose build --no-cache
docker-compose up -d
```

#### 메모리 부족
```bash
# 사용하지 않는 Docker 리소스 정리
docker system prune -a

# 컨테이너 리소스 사용량 확인
docker stats
```

### 데이터 초기화

필요한 경우 모든 데이터를 초기화할 수 있습니다:

```bash
# 컨테이너와 볼륨 완전 삭제
docker-compose down -v

# 이미지도 함께 삭제
docker-compose down -v --rmi all

# 다시 시작
docker-compose up -d
```

### 성능 최적화

```bash
# Docker 리소스 제한 확인
docker-compose config

# 메모리 사용량 모니터링
docker stats --no-stream

# 디스크 사용량 확인
docker system df
```

## 📞 지원

문제가 지속되거나 추가 도움이 필요한 경우:

- **GitHub Issues**: https://github.com/your-repo/RAGIT/issues
- **개발자 가이드**: [SDK 사용법](sdk-usage.md) 참조
- **커뮤니티**: 프로젝트 토론 섹션 활용

---

💡 **개발자이신가요?** 프로젝트를 수정하거나 로컬에서 개발하고 싶다면 [SDK 사용법 가이드](sdk-usage.md)를 참조하세요.