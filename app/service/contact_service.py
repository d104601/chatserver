from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.models.contact import Contact
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import or_

class ContactService:
    @staticmethod
    def search_user_by_email(db: Session, email: str) -> List[Dict[str, Any]]:
        """이메일로 사용자 검색 (부분 일치 지원)"""
        if not email or len(email) < 3:
            raise HTTPException(status_code=400, detail="검색어는 최소 3자 이상이어야 합니다")
            
        users = db.query(User).filter(User.email.like(f"%{email}%")).all()
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in users
        ]
    
    @staticmethod
    def add_contact(db: Session, user_id: int, contact_email: str) -> Dict[str, Any]:
        """연락처에 사용자 추가"""
        # 현재 사용자 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
        # 연락처로 추가할 사용자 확인
        contact_user = db.query(User).filter(User.email == contact_email).first()
        if not contact_user:
            raise HTTPException(status_code=404, detail="추가하려는 연락처 사용자를 찾을 수 없습니다")
            
        # 자기 자신을 연락처로 추가하는 경우 방지
        if user_id == contact_user.id:
            raise HTTPException(status_code=400, detail="자기 자신을 연락처로 추가할 수 없습니다")
            
        # 이미 연락처로 추가되어 있는지 확인
        existing_contact = db.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.contact_id == contact_user.id
        ).first()
        
        if existing_contact:
            raise HTTPException(status_code=400, detail="이미 연락처로 추가된 사용자입니다")
            
        # 새 연락처 추가
        new_contact = Contact(
            user_id=user_id,
            contact_id=contact_user.id
        )
        
        try:
            db.add(new_contact)
            db.commit()
            db.refresh(new_contact)
            
            return {
                "id": new_contact.id,
                "contact": {
                    "id": contact_user.id,
                    "username": contact_user.username,
                    "email": contact_user.email
                },
                "created_at": new_contact.created_at.isoformat()
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"연락처 추가 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def get_user_contacts(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 연락처 목록 조회"""
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
        # 사용자의 연락처 목록 조회
        contacts = db.query(Contact).filter(Contact.user_id == user_id).all()
        
        result = []
        for contact in contacts:
            contact_user = db.query(User).filter(User.id == contact.contact_id).first()
            if contact_user:
                result.append({
                    "id": contact.id,
                    "contact": {
                        "id": contact_user.id,
                        "username": contact_user.username,
                        "email": contact_user.email
                    },
                    "created_at": contact.created_at.isoformat()
                })
                
        return result
    
    @staticmethod
    def remove_contact(db: Session, user_id: int, contact_id: int) -> Dict[str, Any]:
        """연락처에서 사용자 제거"""
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
        # 연락처 찾기
        contact = db.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.id == contact_id
        ).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="삭제할 연락처를 찾을 수 없습니다")
            
        try:
            db.delete(contact)
            db.commit()
            return {"message": "연락처가 성공적으로 삭제되었습니다", "contact_id": contact_id}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"연락처 삭제 중 오류가 발생했습니다: {str(e)}") 