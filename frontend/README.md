# RAG-AGENT 프론트엔드

GitHub 저장소를 지능형 RAG 시스템으로 변환하는 웹 인터페이스

## 🛠️ 기술 스택

- **Python + NiceGUI** - 웹 프레임워크
- **사용자 인증** - 역할 기반 접근 제어
- **RAG 채팅** - AI 기반 저장소 질의응답
- **벡터 DB 관리** - Milvus 연동

## 🚀 사용 방법

### 1. Gateway 서버 시작
먼저 Gateway 서버를 실행해야 합니다:
```bash
cd gateway
run.bat  # Windows
# 또는 python main.py
```

### 2. 프론트엔드 설치 및 실행
```bash
cd frontend
pip install -r requirements.txt
python main.py
```

### 3. 접속
브라우저에서 `http://localhost:8000` 접속

**중요**: Gateway 서버(`localhost:8080`)가 실행되어야 프론트엔드가 정상 작동합니다.

### 3. 데모 계정
- **관리자**: `admin@ragagent.com` / `admin123`
- **사용자**: `user@ragagent.com` / `user123`

## ✨ 주요 기능

- 📁 **저장소 관리** - GitHub 저장소 연동 및 설정
- 💬 **RAG 채팅** - 저장소 내용 기반 AI 대화
- 👥 **멤버 관리** - 역할 변경, 초대, 강퇴
- 🗄️ **벡터 DB** - 임베딩 검색 및 컬렉션 관리
- 📊 **대시보드** - 사용자별 통계 및 활동 내역