from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User  # 임포트 경로 수정
from app.service.user_service import UserService
from typing import Optional


router = APIRouter()

class RegisterRequestBody(BaseModel):
    email: str
    username: str
    password: str

class LoginRequestBody(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str

class LoginResponse(BaseModel):
    message: str
    user: UserResponse

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
    
@router.post("/register", response_model=UserResponse)
def registerUser(request: RegisterRequestBody, db: Session = Depends(get_db)):
    """
    새 사용자를 등록합니다.
    """
    try:
        user = UserService.create_user(
            db=db,
            email=request.email,
            username=request.username,
            password=request.password
        )
        # User 모델을 UserResponse에 맞게 변환
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    except HTTPException as he:
        # HTTPException은 그대로 전달
        raise he
    except Exception as e:
        # 다른 예외는 상세 정보와 함께 500 오류로 변환
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"User registration error: {error_detail}\nTraceback: {error_traceback}"
        )
    
@router.post("/login", response_model=LoginResponse)
def loginUser(request: LoginRequestBody, db: Session = Depends(get_db)):
    try:
        user = UserService.verify_user_credentials(
            db=db,
            email=request.email,
            password=request.password
        )
        # User 모델을 UserResponse에 맞게 변환하여 반환
        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        }
    except HTTPException as he:
        # HTTPException은 그대로 전달
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )
    