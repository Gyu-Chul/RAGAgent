# RAG Agent Gateway

Gateway API 서버로 프론트엔드와 백엔드 서비스 간의 중간 계층 역할을 합니다.

## 시작하기

### 1. 가상환경 생성 및 의존성 설치

```bash
# Windows
run.bat

# 또는 수동으로
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
python main.py
```

서버는 `http://localhost:8080`에서 실행됩니다.

## API 엔드포인트

### 저장소 관련
- `GET /repositories` - 모든 저장소 조회
- `GET /repositories/{repo_id}` - 특정 저장소 조회
- `GET /repositories/{repo_id}/members` - 저장소 멤버 조회

### 채팅 관련
- `GET /repositories/{repo_id}/chat-rooms` - 채팅룸 목록 조회
- `POST /repositories/{repo_id}/chat-rooms` - 새 채팅룸 생성
- `GET /chat-rooms/{chat_room_id}/messages` - 메시지 목록 조회
- `POST /chat-rooms/{chat_room_id}/messages` - 새 메시지 전송

### Vector DB 관련
- `GET /repositories/{repo_id}/vectordb/collections` - 벡터 컬렉션 조회

### 사용자 관련
- `GET /users/{user_email}/active-chats-count` - 활성 채팅 수 조회
- `GET /users/{user_email}/recent-activity` - 최근 활동 조회

## 개발 노트

현재 더미 데이터를 사용하고 있으며, 실제 RAG 처리나 벡터 데이터베이스 연동은 추후 구현 예정입니다.