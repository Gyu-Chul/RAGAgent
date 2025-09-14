# Milvus 관리 가이드

이 프로젝트는 Docker Compose를 사용하여 Milvus를 관리합니다. 

## Doker-compose.yml 파일 다운로드
아래 스크립트를 실행하여 docker 파일을 다운로드합니다.
```bash
bash install_milvus.sh
```

해당 디렉토리에 `docker-compose.yml` 파일이 추가 되었는지 확인합니다.

```bash
the attribute 'version' is obsolete, it will be ignored, please remove it to avoid potential confusion
```
라는 경고 메세지는 기능에 영향을 미치지 않으나, 원한다면 `docker-compose.yml` 파일 상단의 `version: '3.5'`을 삭제하시길 바랍니다.

모든 명령어는 `docker-compose.yml` 파일이 있는 프로젝트 루트 디렉토리에서 실행해주세요.

## Milvus 시작하기
아래 명령어로 Milvus를 백그라운드에서 실행합니다.
```bash
docker compose up -d
```

## 상태 확인
Milvus가 정상적으로 실행되고 있는지 확인합니다.

```bash
docker compose ps
```

## Milvus 중지하기
데이터는 그대로 유지한 채 Milvus를 잠시 멈춥니다.

```Bash
docker compose stop
```

## Milvus 완전히 종료하기
Milvus 컨테이너를 중지하고 삭제합니다.

```Bash
docker compose down
```

## 실시간 로그 보기
Milvus의 실시간 로그를 확인합니다. (종료는 Ctrl+C)

```Bash
docker compose logs -f
```