from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.message import Message
from app.models.user import User
from datetime import datetime
import asyncio
import logging

class MessageService:

    # get all previous messages between two users
    @staticmethod
    async def get_previous_messages(db: Session, user_id: int, other_user_id: int):
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
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get previous messages: {str(e)}"
            )

    @staticmethod
    async def get_messages_between_users(db: Session, user_id: int, other_user_id: int):
        try:
            logging.info(f"메시지 조회 시작: user_id={user_id}, other_user_id={other_user_id}")
            
            # 두 사용자가 존재하는지 확인
            sender = db.query(User).filter(User.id == user_id).first()
            if not sender:
                logging.warning(f"발신자(ID: {user_id})를 찾을 수 없음")
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
                
            receiver = db.query(User).filter(User.id == other_user_id).first()
            if not receiver:
                logging.warning(f"수신자(ID: {other_user_id})를 찾을 수 없음")
                raise HTTPException(status_code=404, detail=f"User with ID {other_user_id} not found")
            
            logging.info(f"사용자 확인 완료: 발신자={sender.username}, 수신자={receiver.username}")
            
            # 두 사용자 간의 메시지 조회
            try:
                messages = db.query(Message).filter(
                    ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
                    ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
                ).order_by(Message.created_at).all()
                
                logging.info(f"메시지 조회 완료: {len(messages)}개 메시지 발견")
                return messages
            except Exception as query_error:
                logging.error(f"메시지 쿼리 중 오류 발생: {str(query_error)}", exc_info=True)
                raise
                
        except HTTPException as he:
            # HTTP 예외는 그대로 전달
            raise he
        except Exception as e:
            logging.error(f"메시지 조회 중 예상치 못한 오류: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get messages: {str(e)}"
            )

    @staticmethod
    async def send_message_to_user(db: Session, message_data):
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
                created_at=datetime.utcnow(),
                is_read=False
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # Socket.IO를 통해 실시간 메시지 전송
            message_payload = {
                "message_id": new_message.id,
                "content": new_message.content,
                "sender_id": new_message.sender_id,
                "receiver_id": new_message.receiver_id,
                "timestamp": new_message.created_at.isoformat(),
                "is_read": new_message.is_read
            }
            
            # 지연 임포트로 원형 참조 방지
            from app.socketio_server import send_personal_message
            
            # 비동기 함수이므로 asyncio.create_task를 통해 호출
            asyncio.create_task(send_personal_message(str(new_message.receiver_id), message_payload))
            
            return new_message
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message: {str(e)}"
            )

    @staticmethod
    async def update_message_read_status(db: Session, message_id: int, user_id: int):
        try:
            # 메시지 조회
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            
            # 권한 체크 - 수신자만 읽음 상태 변경 가능
            if message.receiver_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this message")
            
            # 이미 읽은 상태면 처리하지 않음
            if message.is_read:
                return message
            
            # 읽음 상태 업데이트
            message.is_read = True
            db.commit()
            db.refresh(message)
            
            # Socket.IO를 통해 발신자에게 읽음 상태 알림 (비동기 처리)
            try:
                # 지연 임포트로 원형 참조 방지
                from app.socketio_server import send_personal_message
                
                # 읽음 상태 알림 데이터
                read_notification = {
                    "type": "message_read",
                    "message_id": message.id,
                    "reader_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 비동기 처리
                asyncio.create_task(send_personal_message(str(message.sender_id), read_notification))
            except Exception as e:
                # 소켓 알림 실패는 API 응답에 영향을 주지 않도록 함
                logging.error(f"Failed to send read notification: {str(e)}")
            
            return message
            
        except HTTPException as he:
            # HTTP 예외는 그대로 전달
            raise he
        except Exception as e:
            # 기타 예외는 500 에러로 래핑
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update message read status: {str(e)}"
            )
    