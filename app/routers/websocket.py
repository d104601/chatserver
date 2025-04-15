from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.service.websocket_manager import manager
from app.models.user import User

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    # 사용자 존재 여부 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 웹소켓 연결 수립
    await manager.connect(websocket, user_id)
    
    try:
        # 연결된 사용자에게 큐에 있는 메시지 전송
        queued_messages = manager.get_queued_messages(user_id)
        for message in queued_messages:
            await websocket.send_json(message)

        # 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터의 메시지 처리 (필요한 경우)
            # 예: 읽음 확인, 타이핑 표시 등
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # 연결 종료 시 다른 사용자에게 알림 (선택사항)
        await manager.broadcast({
            "type": "user_disconnected",
            "user_id": user_id
        }) 