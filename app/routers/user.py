from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User  # 임포트 경로 수정
from app.service.user_service import UserService


router = APIRouter()

class RegisterRequestBody(BaseModel):
    email: str
    username: str
    password: str

class LoginRequestBody(BaseModel):
    email: str
    password: str

class RegisterResponse(BaseModel):
    # incomplete. finish this after format is set
    email: str
    username: str
    is_active: bool = True

@router.get("/test")
def userDBTest(db: Session = Depends(get_db)):
    try:
        # DB 연결 테스트 및 첫 번째 사용자 조회
        user = db.query(User).first()
        if not user:
            return {"message": "사용자가 없습니다."}
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 연결 오류: {str(e)}"
        )
    
@router.post("/register")
def registerUser(request: RegisterRequestBody, db: Session = Depends(get_db)):
    try:
        return UserService.create_user(
            db=db,
            email=request.email,
            username=request.username,
            password=request.password
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"User registration error: {str(e)}"
        )
    
@router.post("/login")
def loginUser(request: LoginRequestBody, db: Session = Depends(get_db)):
    try:
        user = UserService.verify_user_credentials(
            db=db,
            email=request.email,
            password=request.password
        )
        return {
            "message": "Login successful",
            "user": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )
    