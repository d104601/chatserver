from fastapi import FastAPI
from app.routers import user, message, websocket
from app.config.database import engine, Base
from app.models.user import User  # User 모델 임포트

app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app.include_router(message.router, prefix="/message", tags=["message"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


# will show all available routes later
@app.get("/")
def read_root():
    return {"Hello": "World"}
