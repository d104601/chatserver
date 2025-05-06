from app.config.database import SessionLocal, engine
from sqlalchemy import text
import logging

logger = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_messages_table():
    """
    메시지 테이블에 is_read 컬럼 추가
    """
    db = SessionLocal()
    try:
        # 기존 컬럼 확인
        check_column = "SELECT 1 FROM pragma_table_info('messages') WHERE name='is_read'"
        result = db.execute(text(check_column)).fetchone()
        
        # is_read 컬럼이 없으면 추가
        if not result:
            logger.info("Adding is_read column to messages table...")
            add_column = "ALTER TABLE messages ADD COLUMN is_read BOOLEAN DEFAULT FALSE NOT NULL"
            db.execute(text(add_column))
            db.commit()
            logger.info("is_read column added successfully")
        else:
            logger.info("is_read column already exists")
            
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting database migration...")
    migrate_messages_table()
    logger.info("Database migration completed") 