from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.service.message_service import MessageService
from app.models.message import Message
from pydantic import BaseModel

router = APIRouter()

class MessageRequest(BaseModel):
    content: str
    sender_id: int
    receiver_id: int

# get messages between two users
@router.get("/getmessages")
async def get_messages(user_id: int, other_user_id: int, db: Session = Depends(get_db)):
    messages = await MessageService.get_messages_between_users(db, user_id, other_user_id)
    return messages

# send message to other user
@router.post("/sendmessage")
async def send_message(message: MessageRequest, db: Session = Depends(get_db)):
    new_message = await MessageService.send_message_to_user(db, message)
    return {"message": "Message sent successfully", "message_id": new_message.id}

