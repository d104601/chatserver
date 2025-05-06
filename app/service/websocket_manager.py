from fastapi import WebSocket, status
from typing import Dict, List, Optional
import json
import logging

# 로깅 설정
logger = logging.getLogger("websocket")

class WebSocketManager:
    def __init__(self):
        # 사용자 ID를 키로, WebSocket 연결을 값으로 저장
        self.active_connections: Dict[int, WebSocket] = {}
        # 각 사용자의 메시지 큐
        self.message_queues: Dict[int, List[dict]] = {}
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """
        사용자 웹소켓 연결 등록
        이미 연결된 경우 기존 연결 종료 후 새 연결 등록
        """
        # 이미 연결된 경우 연결 해제
        if user_id in self.active_connections:
            try:
                logger.info(f"Closing existing connection for user {user_id}")
                await self.active_connections[user_id].close(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason="New connection established"
                )
            except Exception as e:
                logger.error(f"Error closing existing connection: {str(e)}")
            finally:
                self.disconnect(user_id)

        # 새 연결 등록
        self.active_connections[user_id] = websocket
        # 새로운 연결이 생성될 때 메시지 큐 초기화
        if user_id not in self.message_queues:
            self.message_queues[user_id] = []
            
        logger.info(f"User {user_id} connected. Active connections: {len(self.active_connections)}")
        return True

    def disconnect(self, user_id: int) -> bool:
        """사용자 연결 해제"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Active connections: {len(self.active_connections)}")
            return True
        return False

    async def send_personal_message(self, message: dict, user_id: int) -> bool:
        """
        특정 사용자에게 메시지 전송
        사용자가 오프라인이면 큐에 저장
        """
        try:
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_json(message)
                logger.info(f"Message sent to user {user_id}")
                return True
            else:
                # 사용자가 오프라인인 경우 메시지를 큐에 저장
                if user_id not in self.message_queues:
                    self.message_queues[user_id] = []
                self.message_queues[user_id].append(message)
                logger.info(f"Message queued for offline user {user_id}")
                return False
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
            return False

    async def broadcast(self, message: dict) -> int:
        """모든 연결된 클라이언트에게 메시지 전송. 전송 성공 개수 반환"""
        success_count = 0
        for user_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_json(message)
                success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                # 전송 실패한 연결은 제거
                self.disconnect(user_id)
        logger.info(f"Broadcast message sent to {success_count} connections")
        return success_count

    def get_queued_messages(self, user_id: int) -> List[dict]:
        """사용자의 큐에 있는 메시지를 가져오고 큐 비우기"""
        if user_id in self.message_queues:
            messages = self.message_queues[user_id]
            logger.info(f"Retrieved {len(messages)} queued messages for user {user_id}")
            self.message_queues[user_id] = []  # 큐 비우기
            return messages
        return []
    
    def is_user_online(self, user_id: int) -> bool:
        """사용자가 온라인 상태인지 확인"""
        return user_id in self.active_connections

    def get_active_users_count(self) -> int:
        """현재 연결된 사용자 수 반환"""
        return len(self.active_connections)

# 전역 웹소켓 매니저 인스턴스 생성
manager = WebSocketManager() 