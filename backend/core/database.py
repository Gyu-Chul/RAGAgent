from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 의존성 주입을 위한 데이터베이스 세션 생성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 모든 테이블 생성
def create_tables():
    """모든 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)

# 데이터베이스 초기화
def init_db():
    """데이터베이스를 초기화합니다."""
    print("데이터베이스 초기화 중...")

    # UUID 확장 모듈 활성화
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.commit()
            print("UUID 확장 모듈 활성화 완료")
        except Exception as e:
            print(f"UUID 확장 모듈 활성화 중 오류: {e}")

    create_tables()
    print("데이터베이스 초기화 완료!")