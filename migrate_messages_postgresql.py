from app.config.database import SessionLocal, engine
from sqlalchemy import text
import logging

logger = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_messages_table_postgresql():
    """
    PostgreSQL에서 메시지 테이블에 is_read 컬럼 추가
    """
    db = SessionLocal()
    try:
        # 컬럼 존재 여부 확인
        check_column_query = """
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'is_read';
        """
        
        result = db.execute(text(check_column_query)).fetchone()
        
        # is_read 컬럼이 없으면 추가
        if not result:
            logger.info("Adding is_read column to messages table...")
            add_column_query = """
            ALTER TABLE messages 
            ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE;
            """
            db.execute(text(add_column_query))
            db.commit()
            logger.info("is_read column added successfully")
        else:
            logger.info("is_read column already exists")
            
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting PostgreSQL database migration...")
    migrate_messages_table_postgresql()
    logger.info("PostgreSQL database migration completed") 