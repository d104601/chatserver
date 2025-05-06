import socketio
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.models.message import Message
from app.service.message_service import MessageService
from datetime import datetime
import logging
import json
from typing import Dict, List, Any, Optional, Set
import asyncio

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("socketio")

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://localhost:8000', '*'],  # Explicitly add localhost:3000
    logger=logger,
    engineio_logger=logger
)

# Create Socket.IO app
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    socketio_path='socket.io'
)

# User connection information
connected_users: Dict[str, str] = {}  # user_id -> sid
user_sids: Dict[str, str] = {}  # sid -> user_id
message_queues: Dict[str, List[Dict[str, Any]]] = {}  # user_id -> [message objects]

# Global DB session
_db_session = None

# Connection time records
connection_times: Dict[str, datetime] = {}

# Authentication timeout setting (in seconds)
AUTH_TIMEOUT = 30

def get_session():
    # In actual use, it's better to use FastAPI dependency injection,
    # but for Socket.IO we create and use it directly.
    global _db_session
    if _db_session is None:
        # Note: This method is for development only. Production needs separate session management
        from app.config.database import SessionLocal
        _db_session = SessionLocal()
    return _db_session

# Authentication timeout check function
async def check_auth_timeout(sid):
    """Check authentication timeout - disconnect unauthenticated connections after a certain time"""
    try:
        await asyncio.sleep(AUTH_TIMEOUT)
        # Timeout while unauthenticated
        if sid in connection_times and sid not in user_sids:
            connect_time = connection_times[sid]
            current_time = datetime.utcnow()
            time_diff = (current_time - connect_time).total_seconds()
            
            if time_diff >= AUTH_TIMEOUT:
                logger.warning(f"Authentication timeout for {sid} after {time_diff:.1f}s. Disconnecting.")
                await sio.emit('error', {'message': 'Authentication timeout'}, room=sid)
                await sio.disconnect(sid)
    except Exception as e:
        logger.error(f"Error in auth timeout check for {sid}: {str(e)}")

# Connection event
@sio.event
async def connect(sid, environ):
    """Client connection event"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    http_user_agent = environ.get('HTTP_USER_AGENT', 'unknown')
    logger.info(f"Client connected: {sid} from {remote_addr} using {http_user_agent}")
    logger.debug(f"Connection details: {environ}")
    
    # Record connection time (for authentication timeout tracking)
    connection_times[sid] = datetime.utcnow()
    
    # Activate authentication timeout check
    asyncio.create_task(check_auth_timeout(sid))

# Disconnection event
@sio.event
async def disconnect(sid):
    """Client disconnection event"""
    if sid in user_sids:
        user_id = user_sids[sid]
        # Handle disconnection
        if user_id in connected_users:
            del connected_users[user_id]
        del user_sids[sid]
        
        # Notify other users about disconnection
        logger.info(f"User {user_id} disconnected, notifying other users")
        await sio.emit('user_disconnected', {'user_id': user_id}, skip_sid=sid)
    else:
        logger.warning(f"Client {sid} disconnected without authentication")
    
    # Remove connection time information
    if sid in connection_times:
        del connection_times[sid]
    
    logger.info(f"Client disconnected: {sid}")

# Authentication event
@sio.event
async def authenticate(sid, data):
    """User authentication event"""
    try:
        logger.info(f"Authentication attempt from {sid}: {data}")
        user_id = data.get('user_id')
        
        if not user_id:
            logger.warning(f"Authentication failed: Missing user_id from {sid}")
            await sio.emit('error', {'message': 'User ID is required'}, room=sid)
            return
        
        # Check if user exists
        db = get_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Authentication failed: User ID {user_id} not found for {sid}")
                await sio.emit('error', {'message': 'User not found'}, room=sid)
                return
            
            # Remove existing connection if any
            if user_id in connected_users:
                old_sid = connected_users[user_id]
                logger.info(f"Replacing existing connection {old_sid} for user {user_id}")
                await sio.disconnect(old_sid)
            
            # Save connection information
            connected_users[user_id] = sid
            user_sids[sid] = user_id
            
            # Send authentication success response
            logger.info(f"User {user_id} authenticated successfully with sid {sid}")
            await sio.emit('authenticated', {
                'user_id': user_id,
                'username': user.username,
                'status': 'success'
            }, room=sid)
            
            # Send queued messages
            await send_queued_messages(user_id)
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Authentication error for {sid}: {str(e)}", exc_info=True)
        await sio.emit('error', {'message': f'Authentication failed: {str(e)}'}, room=sid)

# Message reception and delivery event
@sio.event
async def message(sid, data):
    """Message reception and delivery event"""
    if sid not in user_sids:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return
    
    try:
        sender_id = user_sids[sid]
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if not receiver_id or not content:
            await sio.emit('error', {'message': 'Receiver ID and content are required'}, room=sid)
            return
        
        # Message delivery logic is handled in message_service
        # Here we only handle direct socket communication
        
        # If receiver is online, send directly
        if receiver_id in connected_users:
            receiver_sid = connected_users[receiver_id]
            await sio.emit('new_message', {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'content': content,
                'timestamp': data.get('timestamp')
            }, room=receiver_sid)
        
        # Send confirmation to sender
        await sio.emit('message_sent', {
            'receiver_id': receiver_id,
            'content': content,
            'timestamp': data.get('timestamp')
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        await sio.emit('error', {'message': 'Failed to process message'}, room=sid)

# Send message to specific user method (for external calls)
async def send_personal_message(user_id: str, message_data: Dict[str, Any]):
    """Send message to specific user"""
    if user_id in connected_users:
        receiver_sid = connected_users[user_id]
        await sio.emit('new_message', message_data, room=receiver_sid)
        return True
    else:
        # If user is offline, add message to queue
        if user_id not in message_queues:
            message_queues[user_id] = []
        message_queues[user_id].append(message_data)
        return False

# Send queued messages method
async def send_queued_messages(user_id: str):
    """Send queued messages"""
    if user_id in message_queues and message_queues[user_id] and user_id in connected_users:
        sid = connected_users[user_id]
        for message in message_queues[user_id]:
            await sio.emit('new_message', message, room=sid)
        message_queues[user_id] = []
        logger.info(f"Sent queued messages to user {user_id}")

# User online status check method
def is_user_online(user_id: str) -> bool:
    """Check if user is online"""
    return user_id in connected_users

# Get active users count method
def get_active_users_count() -> int:
    """Return current connected users count"""
    return len(connected_users)

# Message read status event
@sio.event
async def mark_read(sid, data):
    """Update message read status"""
    try:
        if sid not in user_sids:
            logger.warning(f"Unauthorized mark_read attempt from {sid}")
            return {'status': 'error', 'message': 'Not authenticated'}
            
        user_id = user_sids[sid]
        message_id = data.get('message_id')
        
        if not message_id:
            logger.warning(f"Missing message_id in mark_read from {sid}")
            return {'status': 'error', 'message': 'Missing message_id'}
            
        # Update message read status
        db = get_session()
        try:
            # Check if message exists and if receiver
            message = db.query(Message).filter(Message.id == message_id).first()
            
            if not message:
                logger.warning(f"Message {message_id} not found for mark_read")
                return {'status': 'error', 'message': 'Message not found'}
                
            # Only receiver can update read status
            if message.receiver_id != int(user_id):
                logger.warning(f"User {user_id} attempted to mark someone else's message as read")
                return {'status': 'error', 'message': 'Not authorized to mark this message as read'}
                
            # If already read, handle
            if message.is_read:
                return {'status': 'success', 'message': 'Message already marked as read'}
                
            # Update read status
            message.is_read = True
            db.commit()
            
            logger.info(f"Message {message_id} marked as read by user {user_id}")
            
            # Notify sender about read status (if sender is online)
            sender_id = str(message.sender_id)
            if sender_id in connected_users:
                sender_sid = connected_users[sender_id]
                await sio.emit('message_read', {
                    'message_id': message_id,
                    'reader_id': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sender_sid)
                logger.info(f"Sent read receipt to sender {sender_id}")
            
            return {'status': 'success', 'message': 'Message marked as read'}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in mark_read: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}

# Typing status event
@sio.event
async def typing(sid, data):
    """Send typing status"""
    try:
        if sid not in user_sids:
            return {'status': 'error', 'message': 'Not authenticated'}
            
        user_id = user_sids[sid]
        receiver_id = data.get('receiver_id')
        
        if not receiver_id:
            return {'status': 'error', 'message': 'Missing receiver_id'}
            
        # If receiver is online, send typing status
        if receiver_id in connected_users:
            receiver_sid = connected_users[receiver_id]
            await sio.emit('typing', {
                'user_id': user_id
            }, room=receiver_sid)
            
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Error in typing: {str(e)}")
        return {'status': 'error', 'message': str(e)} 