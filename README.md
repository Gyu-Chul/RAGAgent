# git-ai
Github AI 

# Milvus Docker Setup Guide

이 가이드는 `milvus_docker` 디렉토리 내에 있는 구성 파일을 통해 Milvus Standalone을 Docker Compose로 실행하는 방법을 설명합니다.

## 요구 사항

* WSL2 환경(또는 리눅스)에서 Docker가 설치되어 있고, Docker 서비스가 실행 중이어야 합니다.
* Python이 설치되어 있어야 하며, `pymilvus` 라이브러리가 설치되어 있어야 합니다.


## 1. `docker-compose.yml` 수정

`docker-compose.yml` 파일 안에서 `milvus.yaml` 경로를 수정해야 합니다. Milvus 컨테이너는 설정 파일을 마운트할 때 절대 경로를 요구하므로, 아래 예시처럼 **절대 경로**를 지정해야 합니다.

```yaml
# Ctrl + F + "절대 경로"로 검색 가능
    volumes:
      #################### milvus.yaml의 위치 추가  ####################
      ####################  반드시 절대 경로로 수정   ####################
      - //wsl.localhost/Ubuntu-20.04/home/ubuntu/git-ai/milvus_docker/milvus.yaml
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://etcd:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
```

위 예시에서 `//wsl.localhost/Ubuntu-20.04/home/ubuntu/git-ai/milvus_docker/milvus.yaml` 경로를를 본인의 환경에 맞춰 수정해야 합니다.



## 2. Docker Compose로 Milvus 실행

```bash
# Docker 데몬이 실행 중인지 확인:
sudo service docker status

# Docker가 실행 중이 아니라면 시작:
sudo service docker start

# Milvus Standalone 컨테이너를 백그라운드에서 실행:
sudo docker compose up -d
```

실행 후, 정상적으로 `milvus-standalone`, `milvus-etcd`, `milvus-minio` 컨테이너가 올라왔는지 확인합니다.

```bash
docker ps
```


## 3. 연결 테스트

`connection_test.py` 스크립트를 사용하여 Milvus에 연결이 가능한지 확인합니다.

```bash
# Python 가상환경을 활성화한 상태에서 실행
python connection_test.py
```

출력 결과가 `✅ Milvus 연결 성공! 현재 컬렉션 목록: []` 와 같이 나오면 Milvus가 정상 동작 중인 것입니다.