# 채팅 서버 API

## 기본 정보

- 서버 주소: `http://localhost:8000`
- 웹소켓 주소: `ws://localhost:8000/ws/{user_id}`

## API 엔드포인트

### 사용자 관련 API

#### 회원가입
```
POST /users/register
Content-Type: application/json

Request Body:
{
    "email": "string",
    "username": "string",
    "password": "string"
}
```

#### 로그인
```
POST /users/login
Content-Type: application/json

Request Body:
{
    "email": "string",
    "password": "string"
}
```

#### DB 연결 테스트
```
GET /users/test
```

### 메시지 관련 API

#### 메시지 조회
```
GET /message/getmessages?user_id={int}&other_user_id={int}
```

#### 메시지 전송
```
POST /message/sendmessage
Content-Type: application/json

Request Body:
{
    "content": "string",
    "sender_id": int,
    "receiver_id": int
}
```

### 웹소켓 API

#### 연결
```
ws://localhost:8000/ws/{user_id}
```

#### 메시지 형식

##### 새 메시지
```json
{
    "type": "new_message",
    "message_id": 123,
    "content": "메시지 내용",
    "sender_id": 1,
    "receiver_id": 2,
    "created_at": "2024-03-11T12:00:00Z"
}
```

##### 사용자 연결 종료
```json
{
    "type": "user_disconnected",
    "user_id": 1
}
```

## 개발 환경 설정

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 서버 실행
```bash
uvicorn app.main:app --reload
```

## 주의사항

- 개발 환경에서는 `localhost:8000`에서 실행됩니다.
- 프로덕션 환경에서는 적절한 호스트와 포트로 변경해야 합니다.
- 웹소켓 연결은 사용자 인증이 필요합니다.
- 메시지는 오프라인 사용자에게도 전달되며, 온라인 상태가 되면 자동으로 전송됩니다. 