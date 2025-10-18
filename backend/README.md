# Backend Service - RAGIT

## 목차
- [개요](#개요)
- [아키텍처](#아키텍처)
- [프로젝트 구조](#프로젝트-구조)
- [기술 스택](#기술-스택)
- [핵심 컴포넌트](#핵심-컴포넌트)
- [데이터베이스 설계](#데이터베이스-설계)
- [API 엔드포인트](#api-엔드포인트)

---

## 개요

RAGIT Backend는 **RAG(Retrieval-Augmented Generation) 기반 코드 저장소 분석 플랫폼**의 핵심 API 서버입니다. GitHub 저장소를 분석하고, 벡터 데이터베이스에 저장하여, 사용자가 자연어로 코드베이스에 대해 질문할 수 있도록 지원합니다.

### 주요 기능
- JWT 기반 사용자 인증/인가
- GitHub 저장소 관리 및 비동기 처리
- RAG 기반 Chat 시스템
- Celery를 통한 백그라운드 작업 처리
- 권한 기반 접근 제어 (RBAC)

---

## 아키텍처

### 전체 시스템 아키텍처

```
┌─────────────────┐
│    Frontend     │
└────────┬────────┘
         │ REST API
         ↓
┌─────────────────────────────────────────────┐
│          Backend (FastAPI)                  │
│  ┌───────────────────────────────────────┐ │
│  │     Router Layer                      │ │
│  │  - auth.py (인증)                     │ │
│  │  - repository.py (저장소)             │ │
│  │  - chat.py (채팅)                     │ │
│  └──────────────┬────────────────────────┘ │
│                 │                            │
│  ┌──────────────▼────────────────────────┐ │
│  │     Service Layer                     │ │
│  │  - auth_service.py                    │ │
│  │  - repository_service.py              │ │
│  │  - chat_service.py                    │ │
│  │  - user_service.py                    │ │
│  │  - token_service.py                   │ │
│  │  - password_service.py                │ │
│  └──────────────┬────────────────────────┘ │
│                 │                            │
│  ┌──────────────▼────────────────────────┐ │
│  │     Model Layer (SQLAlchemy)          │ │
│  │  - User, UserSession                  │ │
│  │  - Repository, RepositoryMember       │ │
│  │  - ChatRoom, ChatMessage              │ │
│  │  - VectorCollection                   │ │
│  └──────────────┬────────────────────────┘ │
└─────────────────┼────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
┌───────────────┐   ┌──────────────┐
│  PostgreSQL   │   │    Redis     │
└───────────────┘   └──────┬───────┘
                           │
                           ↓
                  ┌────────────────┐
                  │  RAG Worker    │
                  │  (Celery Task) │
                  └────────────────┘
```

### 계층형 아키텍처 (Layered Architecture)

Backend는 **관심사의 분리(Separation of Concerns)** 원칙에 따라 4개의 주요 계층으로 구성됩니다:

#### 1. Router Layer (라우터 계층)
- **역할**: HTTP 요청/응답 처리
- **책임**: 요청 파라미터 검증, 응답 형식 변환, HTTP 상태 코드 관리
- **위치**: `routers/`
- **특징**: 비즈니스 로직 없이 Service Layer에 위임

#### 2. Service Layer (서비스 계층)
- **역할**: 비즈니스 로직 처리 및 오케스트레이션
- **책임**: 핵심 비즈니스 로직 구현, 여러 모델 간 조율, 트랜잭션 관리
- **위치**: `services/`
- **특징**: 순수 Python 클래스로 테스트 용이

#### 3. Model Layer (모델 계층)
- **역할**: 데이터베이스 모델 정의
- **책임**: ORM 매핑, 테이블 관계 정의, 데이터 제약 조건
- **위치**: `models/`
- **특징**: SQLAlchemy ORM 사용

#### 4. Schema Layer (스키마 계층)
- **역할**: 데이터 직렬화/역직렬화 및 검증
- **책임**: 요청/응답 데이터 검증, 타입 안정성 보장
- **위치**: `schemas/`
- **특징**: Pydantic 모델 사용

---

## 프로젝트 구조

```
backend/
│
├── main.py                    # FastAPI 애플리케이션 진입점
├── config.py                  # 환경 설정 (DB, Redis, JWT)
├── pyproject.toml             # 프로젝트 의존성
├── Dockerfile                 # Docker 이미지 설정
│
├── core/                      # 핵심 인프라
│   ├── database.py           # SQLAlchemy 설정 및 DB 초기화
│   └── celery.py             # Celery 클라이언트 설정
│
├── routers/                   # API 엔드포인트
│   ├── auth.py               # 인증 API (회원가입/로그인/로그아웃)
│   ├── repository.py         # 저장소 API (CRUD, 멤버 관리)
│   └── chat.py               # 채팅 API (ChatRoom, ChatMessage)
│
├── services/                  # 비즈니스 로직
│   ├── auth_service.py       # 인증/인가 오케스트레이션
│   ├── user_service.py       # 사용자 관리
│   ├── token_service.py      # JWT 토큰 생성/검증
│   ├── password_service.py   # 패스워드 해싱/검증
│   ├── session_service.py    # 세션 관리
│   ├── repository_service.py # 저장소 비즈니스 로직
│   └── chat_service.py       # 채팅 비즈니스 로직
│
├── models/                    # 데이터베이스 모델
│   ├── types.py              # 커스텀 타입 (GUID)
│   ├── user.py               # User 모델
│   ├── session.py            # UserSession 모델
│   ├── repository.py         # Repository, RepositoryMember
│   ├── chat.py               # ChatRoom, ChatMessage
│   └── vector.py             # VectorCollection
│
├── schemas/                   # Pydantic 스키마
│   ├── user.py               # User 스키마
│   ├── repository.py         # Repository 스키마
│   └── chat.py               # Chat 스키마
│
└── scripts/                   # DB 마이그레이션 스크립트
    ├── add_file_count_column.py
    └── add_error_message_column.py
```

### 핵심 파일 역할

| 파일 | 역할 |
|------|------|
| `main.py` | FastAPI 앱 생성, 라우터 등록, CORS/로깅 설정 |
| `config.py` | 환경 변수 관리 (DB, Redis, JWT, CORS) |
| `core/database.py` | SQLAlchemy 엔진, 세션 관리, DB 초기화 |
| `core/celery.py` | Celery 클라이언트 설정 (broker, serializer) |

---

## 기술 스택

### 주요 프레임워크

| 카테고리 | 기술 | 버전 | 용도 |
|----------|------|------|------|
| **웹 프레임워크** | FastAPI | ≥0.109.1 | REST API 서버 |
| **ASGI 서버** | Uvicorn | 0.24.0 | 비동기 서버 |
| **ORM** | SQLAlchemy | 2.0.23 | 데이터베이스 ORM |
| **데이터베이스** | PostgreSQL | - | 주 데이터베이스 |
| **데이터 검증** | Pydantic | ≥2.7.4 | 스키마 검증 |
| **인증** | python-jose | 3.3.0 | JWT 토큰 |
| **암호화** | passlib | 1.7.4 | 패스워드 해싱 (bcrypt) |
| **비동기 작업** | Celery | 5.5.3 | 백그라운드 작업 |
| **메시지 브로커** | Redis | 6.4.0 | Celery 브로커 |

---

## 핵심 컴포넌트

### 1. 인증 시스템

#### 인증 플로우

**회원가입 (Signup)**
```
Client → POST /auth/signup
   ↓
AuthService.register_user()
   ├─ 중복 체크 (email, username)
   ├─ PasswordService.create_password_hash()
   └─ DB에 User 저장
```

**로그인 (Login)**
```
Client → POST /auth/login
   ↓
AuthService.login_user()
   ├─ PasswordService.verify_password()
   ├─ TokenService.create_access_token()
   └─ SessionService.create_session()
   ↓
Return: { user, token }
```

**인증된 요청**
```
Client → Request (with Bearer Token)
   ↓
Depends(get_current_active_user)
   ├─ TokenService.verify_access_token()
   ├─ SessionService.get_session_by_token()
   └─ UserService.get_user_by_id()
```

#### JWT 토큰 구조
```json
{
  "sub": "user-uuid",
  "username": "john_doe",
  "exp": 1234567890
}
```
- **Algorithm**: HS256
- **Expiration**: 30분

### 2. Repository 처리 파이프라인

#### 처리 흐름
```
1. Client: Repository 생성 요청 (GitHub URL)
   ↓
2. Backend: Repository 생성 (status: pending)
   ↓
3. Celery Task 전송: process_repository_pipeline
   ↓
4. RAG Worker:
   ├─ Git Clone
   ├─ Python 코드 파싱
   ├─ Vector DB 임베딩
   └─ 상태 업데이트 (status: active)
```

#### Repository 상태 관리
- **status**: `pending` → `syncing` → `active` / `error`
- **vectordb_status**: `pending` → `syncing` → `active` / `error`

**코드 예시 (repository.py:50-58)**
```python
task = celery_app.send_task(
    'rag_worker.tasks.process_repository_pipeline',
    kwargs={
        'repo_id': str(repository.id),
        'git_url': repository.url,
        'repo_name': repository.name
    }
)
```

### 3. Chat 시스템

#### 아키텍처
```
ChatRoom (채팅방)
  ├─ Repository와 1:N
  ├─ User와 N:1
  └─ ChatMessage와 1:N

ChatMessage (메시지)
  ├─ ChatRoom과 N:1
  ├─ sender_type: "user" | "bot"
  └─ sources: JSON (RAG 출처)
```

#### Chat 메시지 처리
```
1. User 메시지 전송 (sender_type: "user")
   ↓
2. Backend: ChatMessage 저장
   ↓
3. Celery Task 전송: chat_query
   ↓
4. RAG Worker:
   ├─ Vector DB 검색 (RAG)
   ├─ LLM 응답 생성
   └─ Bot 메시지 저장 (sender_type: "bot")
```

**코드 예시 (chat.py:252-260)**
```python
if message_data.sender_type == "user":
    task = celery_app.send_task(
        'rag_worker.tasks.chat_query',
        kwargs={
            'chat_room_id': str(chat_room.id),
            'repo_id': str(chat_room.repository_id),
            'user_message': message.content,
            'top_k': 5
        }
    )
```

### 4. 비동기 작업 처리 (Celery)

#### Celery 아키텍처
```
Backend (FastAPI) → Redis (Broker) → RAG Worker (Celery)
      ↓                   ↓                    ↓
   send_task()      Task 큐 저장         Task 실행
```

#### 주요 Celery Task

| Task 이름 | 트리거 시점 | 작업 내용 |
|-----------|------------|-----------|
| `process_repository_pipeline` | Repository 생성 시 | Git Clone → 파싱 → 벡터화 |
| `chat_query` | 사용자 메시지 생성 시 | RAG 검색 → LLM 응답 생성 |

#### Celery 설정 (core/celery.py)
```python
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    task_time_limit=30 * 60,  # 30분
)
```

### 5. 권한 관리 (RBAC)

#### 권한 계층
```
System Level:
├─ admin (전체 시스템 관리)
└─ user (일반 사용자)

Repository Level:
├─ owner (소유자 - 모든 권한)
├─ admin (관리자 - 멤버 관리, 설정)
├─ member (멤버 - 읽기/쓰기)
└─ viewer (뷰어 - 읽기만)
```

#### 권한 검증 (repository_service.py:163-207)
```python
def check_user_permission(db, repo_id, user_id, required_role=None):
    # 1. 소유자 확인
    if repo.owner_id == user_uuid:
        return True

    # 2. 멤버 확인
    member = db.query(RepositoryMember).filter(...).first()

    # 3. 역할 확인 (viewer < member < admin)
    role_hierarchy = {"viewer": 0, "member": 1, "admin": 2}
    return user_role_level >= required_role_level
```

---

## 데이터베이스 설계

### ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│      User       │
│  - id (PK)      │
│  - username     │
│  - email        │
│  - password     │
└────────┬────────┘
         │ 1:N
         ├────────────────┐
         │                │
    ┌────▼──────────┐ ┌──▼────────────────┐
    │ UserSession   │ │  Repository       │
    │               │ │  - status         │
    │               │ │  - vectordb_status│
    └───────────────┘ └──┬────────────────┘
                         │ 1:N
                         ├─────────────┐
                         │             │
                    ┌────▼──────┐ ┌───▼──────────┐
                    │ ChatRoom  │ │RepositoryMember│
                    └────┬──────┘ └───────────────┘
                         │ 1:N
                    ┌────▼──────────┐
                    │ ChatMessage   │
                    │ - sender_type │
                    │ - sources     │
                    └───────────────┘
```

### 주요 테이블

#### users
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID (PK) | 사용자 ID |
| username | VARCHAR(50) | 사용자명 (유니크) |
| email | VARCHAR(100) | 이메일 (유니크) |
| hashed_password | VARCHAR(255) | bcrypt 해싱 패스워드 |
| role | VARCHAR(20) | 역할 (user, admin) |
| is_active | BOOLEAN | 활성화 상태 |

#### repositories
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID (PK) | 저장소 ID |
| name | VARCHAR(100) | 저장소 이름 |
| url | VARCHAR(255) | Git URL |
| owner_id | UUID (FK) | 소유자 ID |
| status | VARCHAR(20) | pending/syncing/active/error |
| vectordb_status | VARCHAR(20) | 벡터 DB 상태 |
| file_count | INTEGER | 파싱된 파일 개수 |

#### chat_rooms
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID (PK) | 채팅방 ID |
| name | VARCHAR(100) | 채팅방 이름 |
| repository_id | UUID (FK) | 연결된 저장소 |
| created_by | UUID (FK) | 생성자 |
| message_count | INTEGER | 메시지 개수 |

#### chat_messages
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID (PK) | 메시지 ID |
| chat_room_id | UUID (FK) | 채팅방 ID |
| sender_id | UUID (FK, NULL) | 발신자 (bot은 NULL) |
| sender_type | VARCHAR(10) | user / bot |
| content | TEXT | 메시지 내용 |
| sources | TEXT | RAG 출처 (JSON) |

---

## API 엔드포인트

### 인증 API (`/auth`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/auth/signup` | 회원가입 | ✗ |
| POST | `/auth/login` | 로그인 | ✗ |
| POST | `/auth/logout` | 로그아웃 | ✓ |
| GET | `/auth/me` | 현재 사용자 정보 | ✓ |
| GET | `/auth/users/search?email={email}` | 사용자 검색 | ✓ |

**예시: 로그인**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@ragit.com",
  "password": "user123"
}
```

**응답**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "username": "user",
    "email": "user@ragit.com",
    "role": "user"
  },
  "token": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### Repository API (`/api/repositories`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/api/repositories/` | Repository 생성 | ✓ |
| GET | `/api/repositories/` | 사용자 Repository 목록 | ✓ |
| GET | `/api/repositories/{repo_id}` | Repository 조회 | ✓ |
| GET | `/api/repositories/{repo_id}/status` | 처리 상태 조회 | ✓ |
| PUT | `/api/repositories/{repo_id}` | Repository 수정 | ✓ (admin) |
| DELETE | `/api/repositories/{repo_id}` | Repository 삭제 | ✓ (owner) |
| GET | `/api/repositories/{repo_id}/members` | 멤버 목록 | ✓ |
| POST | `/api/repositories/{repo_id}/members` | 멤버 추가 | ✓ (admin) |

**예시: Repository 생성**
```http
POST /api/repositories/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "my-project",
  "description": "My awesome project",
  "url": "https://github.com/user/my-project",
  "is_public": false
}
```

### Chat API (`/api/repositories`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/api/repositories/{repo_id}/chat-rooms` | ChatRoom 생성 | ✓ |
| GET | `/api/repositories/{repo_id}/chat-rooms` | ChatRoom 목록 | ✓ |
| GET | `/api/repositories/chat-rooms/{room_id}` | ChatRoom 조회 | ✓ |
| DELETE | `/api/repositories/chat-rooms/{room_id}` | ChatRoom 삭제 | ✓ (creator) |
| POST | `/api/repositories/chat-rooms/{room_id}/messages` | 메시지 전송 | ✓ |
| GET | `/api/repositories/chat-rooms/{room_id}/messages` | 메시지 목록 | ✓ |

**예시: 메시지 전송**
```http
POST /api/repositories/chat-rooms/{room_id}/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "chat_room_id": "room-uuid",
  "sender_type": "user",
  "content": "What is the main.py file for?"
}
```

---

### 기본 계정

| 이메일 | 비밀번호 | 역할 |
|--------|----------|------|
| admin@ragit.com | admin123 | admin |
| user@ragit.com | user123 | user |

---
