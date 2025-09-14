#!/bin/bash

# 스크립트의 목적을 설명하는 메시지 출력
echo "Milvus Standalone 설치를 시작합니다..."

# 1. docker-compose.yml 파일 다운로드
echo "docker-compose.yml 파일을 다운로드합니다..."
curl -L "https://github.com/milvus-io/milvus/releases/download/v2.6.0/milvus-standalone-docker-compose.yml" -o docker-compose.yml

# 다운로드 성공 여부 확인
if [ $? -ne 0 ]; then
    echo "파일 다운로드에 실패했습니다. 스크립트를 종료합니다."
    exit 1
fi

# 2. Docker Compose를 사용하여 Milvus 실행
echo "Milvus 컨테이너를 백그라운드에서 실행합니다..."
docker compose up -d

# 실행 성공 여부 확인
if [ $? -ne 0 ]; then
    echo "Milvus 실행에 실패했습니다. Docker가 실행 중인지, 권한 문제가 없는지 확인하세요."
    exit 1
fi

# 3. 최종 확인 및 완료 메시지
echo "Milvus 컨테이너 상태를 확인합니다. (3개의 컨테이너가 'Up' 상태여야 합니다)"
sleep 5 # 컨테이너가 완전히 시작될 때까지 잠시 대기
docker compose ps

echo ""
echo "Milvus 설치 및 실행이 완료되었습니다! 🎉"
