# 코딩 규칙

## 필수 준수 사항 (3가지)

### 1. 단일 책임 원칙 (Single Responsibility Principle)
- **규칙**: 각 클래스/함수는 단 하나의 책임만 가져야 함
- **적용**: 기능별로 명확하게 분리하여 구현

```python
# ❌ 나쁜 예: 여러 책임을 가진 클래스
class UserManager:
    def create_user(self): pass
    def send_email(self): pass
    def log_activity(self): pass

# ✅ 좋은 예: 책임별로 분리된 클래스
class UserService:
    def create_user(self): pass

class EmailService:
    def send_email(self): pass

class ActivityLogger:
    def log_activity(self): pass
```

### 2. 인터페이스 분리 원칙 (Interface Segregation Principle)
- **규칙**: 클라이언트는 사용하지 않는 인터페이스에 의존하면 안 됨
- **적용**: 필요한 기능만 노출하는 최소 인터페이스 설계

```python
# ❌ 나쁜 예: 거대한 범용 인터페이스
class DatabaseInterface:
    def read(self): pass
    def write(self): pass
    def backup(self): pass
    def migrate(self): pass

# ✅ 좋은 예: 목적별로 분리된 인터페이스
class ReadableInterface:
    def read(self): pass

class WritableInterface:
    def write(self): pass

class BackupInterface:
    def backup(self): pass
```

### 3. 타입 어노테이션 필수 작성
- **규칙**: 모든 함수, 메서드, 변수에 타입 어노테이션 필수
- **적용**: 매개변수, 반환값, 클래스 속성 모두 타입 명시

```python
# ❌ 나쁜 예: 타입 어노테이션 없음
def process_user(user_data, options):
    return user_data.get('name')

# ✅ 좋은 예: 타입 어노테이션 있음
from typing import Dict, Any, Optional

def process_user(user_data: Dict[str, Any], options: Dict[str, bool]) -> Optional[str]:
    return user_data.get('name')

class UserService:
    def __init__(self, database_url: str) -> None:
        self.database_url: str = database_url

    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        return {"id": 1, "name": name, "email": email}
```

---

**이 3가지 규칙은 해당 프로젝트에서 코드를 작성할 때 반드시 준수해야 하는 필수 사항입니다.**