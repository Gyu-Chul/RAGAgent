#!/bin/bash
set -e

echo "🚀 RAGIT Docker 기반 설치 스크립트"
echo "=================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "   설치 가이드: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "   설치 가이드: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 환경 확인됨"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker 데몬이 실행되지 않았습니다."
    echo "   Docker Desktop을 시작하거나 다음 명령어를 실행하세요:"
    echo "   sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker 데몬 실행 중"

# Create environment file for Docker
if [ ! -f ".env.docker" ]; then
    echo "📝 Docker 환경 설정 파일 생성 중..."
    cat > .env.docker << EOF
# Database Configuration (Docker internal network)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragit

# Redis Configuration (Docker internal network)
REDIS_URL=redis://redis:6379/0

# JWT Configuration
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=["http://localhost:8000"]

# Docker specific settings
POSTGRES_DB=ragit
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
EOF
    echo "✅ .env.docker 파일이 생성되었습니다."
fi

# Build Docker images
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build

# Create data directory for persistence
mkdir -p ./data

echo "🐳 Docker 컨테이너 시작 중..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ 서비스 준비 대기 중..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ RAGIT Docker 배포가 완료되었습니다!"
    echo ""
    echo "🎯 서비스 상태:"
    docker-compose ps
    echo ""
    echo "📋 관리 명령어:"
    echo "   시작: docker-compose up -d"
    echo "   중지: docker-compose down"
    echo "   로그: docker-compose logs -f"
    echo "   재시작: docker-compose restart"
    echo ""
    echo "🌐 웹 인터페이스: http://localhost:8000"
    echo "🔗 백엔드 API: http://localhost:8001"
    echo "🚪 게이트웨이: http://localhost:8080"
else
    echo "❌ 일부 서비스가 제대로 시작되지 않았습니다."
    echo "로그를 확인하세요: docker-compose logs"
fi