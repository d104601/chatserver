from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import time
import logging
from sqlalchemy.exc import OperationalError

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# .env 파일 로드
load_dotenv()

# 환경변수에서 DB 접속 정보 가져오기
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5431")
DB_NAME = os.getenv("DB_NAME", "chatdb")

# DB URL 구성
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 데이터베이스 연결 재시도 함수
def create_db_engine(url, max_retries=10, retry_interval=30):
    retries = 0
    
    while retries < max_retries:
        try:
            logger.info(f"Connecting to the database... (Try {retries + 1}/{max_retries})")
            engine = create_engine(url)
            # 연결 테스트
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful!")
            return engine
        except OperationalError as e:
            retries += 1
            logger.error(f"Database connection failed: {str(e)}")
            if retries < max_retries:
                logger.info(f"{retry_interval} seconds later, retrying...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Reached the maximum number of retries ({max_retries}). Exiting the server.")
                raise

# 엔진 생성
engine = create_db_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()