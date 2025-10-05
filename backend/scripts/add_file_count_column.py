"""
파일 개수 컬럼 추가 마이그레이션 스크립트
단일 책임: repositories 테이블에 file_count 컬럼 추가
"""

from sqlalchemy import create_engine, text
from ..config import DATABASE_URL

def add_file_count_column() -> None:
    """repositories 테이블에 file_count 컬럼 추가"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            # file_count 컬럼 추가 (이미 존재하면 무시)
            conn.execute(text("""
                ALTER TABLE repositories
                ADD COLUMN IF NOT EXISTS file_count INTEGER DEFAULT 0;
            """))
            conn.commit()
            print("✅ file_count 컬럼 추가 완료")
        except Exception as e:
            print(f"❌ 컬럼 추가 실패: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_file_count_column()
