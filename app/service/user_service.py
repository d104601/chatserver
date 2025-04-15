from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
import bcrypt


class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, email: str, username: str, password: str):
        # 이메일 중복 확인
        if UserService.get_user_by_email(db, email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # 비밀번호 해싱
        hashed_password = UserService.hash_password(password)
        
        # 새 사용자 생성
        new_user = User(
            email=email,
            username=username,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def verify_user_credentials(db: Session, email: str, password: str):
        user = UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        if not UserService.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid password")
        
        return user

    @staticmethod
    def hash_password(password: str) -> str:
        # 비밀번호를 바이트로 변환
        password_bytes = password.encode('utf-8')
        # 솔트 생성 및 비밀번호 해싱
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # 해시된 비밀번호를 문자열로 변환하여 반환
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # 입력된 비밀번호와 해시된 비밀번호를 바이트로 변환
        plain_password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        # 비밀번호 검증
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes) 