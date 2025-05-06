from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.service.contact_service import ContactService
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any

router = APIRouter()

class ContactSearchRequest(BaseModel):
    email: str

class ContactAddRequest(BaseModel):
    contact_email: EmailStr

class ContactResponse(BaseModel):
    id: int
    contact: dict
    created_at: str

class UserSearchResponse(BaseModel):
    id: int
    username: str
    email: str

@router.get("/search")
async def search_user(email: str, db: Session = Depends(get_db)):
    """이메일로 사용자 검색 (부분 일치 지원)"""
    try:
        users = ContactService.search_user_by_email(db, email)
        return users
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 검색 중 오류가 발생했습니다: {str(e)}")

@router.post("/add")
async def add_contact(request: ContactAddRequest, user_id: int = Query(...), db: Session = Depends(get_db)):
    """연락처에 사용자 추가"""
    try:
        result = ContactService.add_contact(db, user_id, request.contact_email)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연락처 추가 중 오류가 발생했습니다: {str(e)}")

@router.get("/list")
async def list_contacts(user_id: int = Query(...), db: Session = Depends(get_db)):
    """사용자의 연락처 목록 조회"""
    try:
        contacts = ContactService.get_user_contacts(db, user_id)
        return contacts
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연락처 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/remove")
async def remove_contact(user_id: int = Query(...), contact_id: int = Query(...), db: Session = Depends(get_db)):
    """연락처에서 사용자 제거"""
    try:
        result = ContactService.remove_contact(db, user_id, contact_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연락처 삭제 중 오류가 발생했습니다: {str(e)}") 