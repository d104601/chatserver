from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        # 사용자 ID를 키로, WebSocket 연결을 값으로 저장
        self.active_connections: Dict[int, WebSocket] = {}
        # 각 사용자의 메시지 큐
        self.message_queues: Dict[int, List[dict]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        # 새로운 연결이 생성될 때 메시지 큐 초기화
        if user_id not in self.message_queues:
            self.message_queues[user_id] = []

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.message_queues:
            del self.message_queues[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
        else:
            # 사용자가 오프라인인 경우 메시지를 큐에 저장
            if user_id not in self.message_queues:
                self.message_queues[user_id] = []
            self.message_queues[user_id].append(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def get_queued_messages(self, user_id: int) -> List[dict]:
        if user_id in self.message_queues:
            messages = self.message_queues[user_id]
            self.message_queues[user_id] = []  # 큐 비우기
            return messages
        return []

# 전역 웹소켓 매니저 인스턴스 생성
manager = WebSocketManager() 