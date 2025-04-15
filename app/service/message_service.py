from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.message import Message
from app.models.user import User
from datetime import datetime
from app.service.websocket_manager import manager

class MessageService:
    @staticmethod
    async def get_messages_between_users(db: Session, user_id: int, other_user_id: int):
        try:
            # 두 사용자가 존재하는지 확인
            sender = db.query(User).filter(User.id == user_id).first()
            receiver = db.query(User).filter(User.id == other_user_id).first()
            
            if not sender or not receiver:
                raise HTTPException(status_code=404, detail="User not found")
            
            # 두 사용자 간의 메시지 조회
            messages = db.query(Message).filter(
                ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
                ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
            ).order_by(Message.created_at).all()
            
            return messages
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get messages: {str(e)}"
            )

    @staticmethod
    async def send_message_to_user(db: Session, message_data: dict):
        try:
            # 발신자와 수신자가 존재하는지 확인
            sender = db.query(User).filter(User.id == message_data.sender_id).first()
            receiver = db.query(User).filter(User.id == message_data.receiver_id).first()
            
            if not sender or not receiver:
                raise HTTPException(status_code=404, detail="User not found")
            
            # 새 메시지 생성
            new_message = Message(
                content=message_data.content,
                sender_id=message_data.sender_id,
                receiver_id=message_data.receiver_id,
                created_at=datetime.utcnow()
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # 웹소켓을 통해 실시간 메시지 전송
            message_payload = {
                "type": "new_message",
                "message_id": new_message.id,
                "content": new_message.content,
                "sender_id": new_message.sender_id,
                "receiver_id": new_message.receiver_id,
                "created_at": new_message.created_at.isoformat()
            }
            
            # 수신자에게 메시지 전송
            await manager.send_personal_message(message_payload, new_message.receiver_id)
            
            return new_message
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message: {str(e)}"
            )
