from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "client_encoding": "utf8",
        "application_name": "ragit_backend"
    },
    echo=False
)

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

    try:
        # UUID 확장 모듈 활성화 (선택적)
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
                conn.commit()
                print("UUID 확장 모듈 활성화 완료")
            except Exception as e:
                print(f"UUID 확장 모듈 활성화 중 오류: {e}")

        create_tables()
        print("데이터베이스 테이블 생성 완료!")

        # 마이그레이션: file_count 컬럼 추가
        _add_missing_columns()

        # 기본 사용자 생성
        _create_default_users()

        print("데이터베이스 초기화 완료!")
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")
        print("데이터베이스 없이 계속 진행합니다...")


def _add_missing_columns():
    """누락된 컬럼 추가 (마이그레이션)"""
    print("데이터베이스 스키마 마이그레이션 중...")

    with engine.connect() as conn:
        try:
            # repositories 테이블에 file_count 컬럼 추가
            conn.execute(text("""
                ALTER TABLE repositories
                ADD COLUMN IF NOT EXISTS file_count INTEGER DEFAULT 0;
            """))
            conn.commit()
            print("✅ repositories.file_count 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️  file_count 컬럼 추가 중 오류 (무시 가능): {e}")
            conn.rollback()

        try:
            # repositories 테이블에 error_message 컬럼 추가
            conn.execute(text("""
                ALTER TABLE repositories
                ADD COLUMN IF NOT EXISTS error_message TEXT;
            """))
            conn.commit()
            print("✅ repositories.error_message 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️  error_message 컬럼 추가 중 오류 (무시 가능): {e}")
            conn.rollback()


def _create_default_users():
    """기본 사용자(admin, user) 생성"""
    from ..models import User
    from ..services.password_service import default_password_service

    db = SessionLocal()
    try:
        # Admin 계정 확인 및 생성
        admin_user = db.query(User).filter(User.email == "admin@ragit.com").first()
        if not admin_user:
            print("기본 관리자 계정 생성 중...")
            admin_password_hash = default_password_service.create_password_hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@ragit.com",
                hashed_password=admin_password_hash,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            print("✅ Admin 계정 생성 완료 (admin@ragit.com / admin123)")
        else:
            print("ℹ️  Admin 계정이 이미 존재합니다.")

        # User 계정 확인 및 생성
        normal_user = db.query(User).filter(User.email == "user@ragit.com").first()
        if not normal_user:
            print("기본 사용자 계정 생성 중...")
            user_password_hash = default_password_service.create_password_hash("user123")
            normal_user = User(
                username="user",
                email="user@ragit.com",
                hashed_password=user_password_hash,
                role="user",
                is_active=True
            )
            db.add(normal_user)
            print("✅ User 계정 생성 완료 (user@ragit.com / user123)")
        else:
            print("ℹ️  User 계정이 이미 존재합니다.")

        db.commit()
        print("기본 사용자 생성 완료!")

    except Exception as e:
        print(f"기본 사용자 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()