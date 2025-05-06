from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.service.websocket_manager import manager
from app.models.user import User
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()  # 먼저 연결을 수락
    
    try:
        # 사용자 존재 여부 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # WebSocket에서는 HTTP 예외 대신 close로 연결 종료
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return  # 연결 종료 후 함수 종료
        
        # 웹소켓 연결 관리자에 등록
        await manager.connect(websocket, user_id)
        
        # 연결된 사용자에게 큐에 있는 메시지 전송
        queued_messages = manager.get_queued_messages(user_id)
        for message in queued_messages:
            await websocket.send_json(message)
        
        # 연결 성공 메시지 전송
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Successfully connected to websocket"
        })

        # 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터의 메시지 처리 (필요한 경우)
            # 예: 읽음 확인, 타이핑 표시 등
            # JSON 형식의 데이터로 파싱해 처리할 수도 있음
            try:
                parsed_data = json.loads(data)
                # 여기서 메시지 타입에 따라 처리할 수 있음
            except json.JSONDecodeError:
                # 텍스트 그대로 처리
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # 연결 종료 시 다른 사용자에게 알림 (선택사항)
        await manager.broadcast({
            "type": "user_disconnected",
            "user_id": user_id
        })
    except Exception as e:
        # 기타 예외 처리
        if websocket.client_state.CONNECTED:  # 연결이 아직 활성 상태인 경우
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        # 연결이 이미 관리자에 등록된 경우 연결 해제
        if user_id in manager.active_connections:
            manager.disconnect(user_id) 