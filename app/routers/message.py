from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.service.message_service import MessageService
from app.models.message import Message
from pydantic import BaseModel
import logging

router = APIRouter()

class MessageRequest(BaseModel):
    content: str
    sender_id: int
    receiver_id: int

# get all previous messages between two users
@router.get("/getpreviousmessages")
async def get_previous_messages(user_id: int, other_user_id: int, db: Session = Depends(get_db)):
    try:
        messages = await MessageService.get_previous_messages(db, user_id, other_user_id)
        
        # 메시지 객체를 직렬화 가능한 사전으로 변환
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "created_at": msg.created_at.isoformat(),
                "is_read": msg.is_read
            })
        
        return message_list
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"이전 메시지 조회 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve previous messages: {str(e)}")

# get messages between two users
@router.get("/getmessages")
async def get_messages(user_id: int, other_user_id: int, db: Session = Depends(get_db)):
    try:
        messages = await MessageService.get_messages_between_users(db, user_id, other_user_id)
        
        # 메시지 객체를 직렬화 가능한 사전으로 변환
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "created_at": msg.created_at.isoformat(),
                "is_read": msg.is_read
            })
        
        return message_list
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"메시지 조회 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")

# send message to other user
@router.post("/sendmessage")
async def send_message(message: MessageRequest, db: Session = Depends(get_db)):
    new_message = await MessageService.send_message_to_user(db, message)
    return {"message": "Message sent successfully", "message_id": new_message.id}

# update message status to read
@router.put("/updatemessagereadstatus")
async def update_message_read_status(message_id: int, user_id: int, db: Session = Depends(get_db)):
    """메시지 읽음 상태 업데이트 (수신자만 가능)"""
    try:
        updated_message = await MessageService.update_message_read_status(db, message_id, user_id)
        return {
            "status": "success",
            "message": "Message read status updated successfully",
            "data": {
                "message_id": updated_message.id,
                "content": updated_message.content,
                "sender_id": updated_message.sender_id,
                "receiver_id": updated_message.receiver_id,
                "created_at": updated_message.created_at.isoformat(),
                "is_read": updated_message.is_read
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


