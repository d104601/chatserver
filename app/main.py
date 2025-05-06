from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine, Base, SessionLocal
import logging
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
import time
import json
# 추가: Socket.IO를 위한 임포트
import socketio
from app.socketio_server import sio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# 모델 임포트 - 순서 중요 (의존성 있는 모델은 나중에 임포트)
from app.models.user import User
from app.models.message import Message
from app.models.contact import Contact

# 라우터 임포트
from app.routers import user, message, websocket, contact

app = FastAPI()

# Socket.IO를 FastAPI 앱에 마운트
app.mount('/socket.io', socketio.ASGIApp(sio, socketio_path=''))

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],  # localhost:3000 명시적 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 연결 상태 확인
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        # 데이터베이스 연결 상태 테스트
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return Response(
            content=json.dumps({"detail": "Database connection error. Please try again later."}), 
            status_code=503,
            media_type="application/json"
        )
    
    response = await call_next(request)
    return response

# 데이터베이스 테이블 생성
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
except SQLAlchemyError as e:
    logger.error(f"Error creating database tables: {str(e)}")
    # 이 오류는 치명적이지만, 앱은 계속 실행됩니다.
    # DB 연결이 복구되었을 때 다시 시도할 수 있습니다.

app.include_router(message.router, prefix="/message", tags=["message"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(contact.router, prefix="/contacts", tags=["contacts"])

# will show all available routes later
@app.get("/")
def read_root():
    return {"Hello": "World"}
