# Chat Server API

## Basic Information

- Server Address: `http://localhost:8000`
- Socket.IO Address: `http://localhost:8000/socket.io`

## API Endpoints

### User Related APIs

#### Registration
```
POST /users/register
Content-Type: application/json

Request Body:
{
    "email": "string",
    "username": "string",
    "password": "string"
}

Response:
{
    "id": int,
    "email": "string",
    "username": "string"
}
```

#### Login
```
POST /users/login
Content-Type: application/json

Request Body:
{
    "email": "string",
    "password": "string"
}

Response:
{
    "message": "Login successful",
    "user": {
        "id": int,
        "email": "string",
        "username": "string"
    }
}
```

#### DB Connection Test
```
GET /users/test

Response:
{
    "message": "No users found." // or first user information found
}
```

### Message Related APIs

#### Get Messages
```
GET /message/getmessages?user_id={int}&other_user_id={int}

Response:
[
    {
        "id": int,
        "content": "string",
        "sender_id": int,
        "receiver_id": int,
        "created_at": "string (ISO format)"
    },
    ...
]
```

#### Get Previous Messages
```
GET /message/getpreviousmessages?user_id={int}&other_user_id={int}

Response:
[
    {
        "id": int,
        "content": "string",
        "sender_id": int,
        "receiver_id": int,
        "created_at": "string (ISO format)",
        "is_read": boolean
    },
    ...
]
```

#### Send Message
```
POST /message/sendmessage
Content-Type: application/json

Request Body:
{
    "content": "string",
    "sender_id": int,
    "receiver_id": int
}

Response:
{
    "message": "Message sent successfully",
    "message_id": int
}
```

#### Update Message Read Status
```
PUT /message/updatemessagereadstatus?message_id={int}&user_id={int}

Response:
{
    "status": "success",
    "message": "Message read status updated successfully",
    "data": {
        "message_id": int,
        "content": "string",
        "sender_id": int,
        "receiver_id": int,
        "created_at": "string (ISO format)",
        "is_read": true
    }
}
```

### Contact Related APIs

#### Search Users by Email (Partial Match Supported)
```
GET /contacts/search?email={string}

Response:
[
  {
    "id": int,
    "username": "string",
    "email": "string"
  },
  ...
]
```

#### Add User to Contacts
```
POST /contacts/add?user_id={int}
Content-Type: application/json

Request Body:
{
    "contact_email": "string"
}

Response:
{
    "id": int,
    "contact": {
        "id": int,
        "username": "string",
        "email": "string"
    },
    "created_at": "string (ISO format)"
}
```

#### Get Contact List
```
GET /contacts/list?user_id={int}

Response:
[
    {
        "id": int,
        "contact": {
            "id": int,
            "username": "string",
            "email": "string"
        },
        "created_at": "string (ISO format)"
    },
    ...
]
```

#### Remove User from Contacts
```
DELETE /contacts/remove?user_id={int}&contact_id={int}
```

### Socket.IO API

#### Connection
```javascript
import { io } from "socket.io-client";

// Debugging activation
localStorage.debug = '*';  // Socket.IO debug log activation

// Connection options setting
const socket = io("http://localhost:8000", {
  path: "/socket.io",
  reconnection: true,
  reconnectionAttempts: 3,   // Maximum 3 reconnection attempts
  reconnectionDelay: 2000,   // Wait 2 seconds before first reconnection attempt
  timeout: 10000,            // Connection attempt timeout 10 seconds
  autoConnect: false,        // Start connection manually
});

// Connection related logs
console.log("Socket.IO client initialization");

// Start connection manually
console.log("Socket.IO connection attempt...");
socket.connect();

// Connection status tracking
let isAuthenticated = false;
let userId = "123"; // Need to change to actual user ID

// Connection events
socket.on("connect", () => {
  console.log("Socket.IO connected to server:", socket.id);
  
  // Authentication attempt
  console.log("Authentication attempt in progress...");
  socket.emit("authenticate", { user_id: userId });
});

// Authentication success
socket.on("authenticated", (data) => {
  console.log("Authentication success:", data);
  isAuthenticated = true;
  
  // Start app logic after success
  // startApp();
});

// Connection error
socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
  // Stop reconnection if error persists
  if (socket.reconnectionAttempts >= 3) {
    console.log("Maximum reconnection attempt count exceeded, stopping");
    socket.disconnect();
  }
});

// Server error
socket.on("error", (error) => {
  console.error("Server error:", error);
  
  // Try re-authentication if it's an authentication error or stop reconnection
  if (error.message && error.message.includes("Authentication")) {
    console.error("Authentication error, stopping reconnection");
    socket.disconnect();
  }
});

// Disconnection
socket.on("disconnect", (reason) => {
  console.log("Disconnected:", reason);
  isAuthenticated = false;
  
  // If the server explicitly disconnects the connection
  if (reason === "io server disconnect") {
    console.log("Server connection ended, manual reconnection needed");
    // Try reconnect after timeout
    setTimeout(() => {
      console.log("Manual reconnection attempt...");
      socket.connect();
    }, 5000);
  }
  
  // If the client disconnects the connection
  if (reason === "io client disconnect") {
    console.log("Client connection ended, no reconnection attempt");
  }
});

// Cleanup function
function cleanup() {
  console.log("Cleaning up connection...");
  socket.disconnect();
}

// Clean up before page unload
window.addEventListener("beforeunload", cleanup);
```

#### Event List

##### Client to Server Events

1. **authenticate** - User Authentication
```javascript
socket.emit("authenticate", { user_id: "123" });
```

2. **message** - Message Sending
```javascript
socket.emit("message", {
  receiver_id: "456",
  content: "안녕하세요",
  timestamp: new Date().toISOString()
});
```

3. **mark_read** - Message Read Status Marking
```javascript
socket.emit("mark_read", { message_id: "789" });
```

4. **typing** - Typing Status Sending
```javascript
socket.emit("typing", { receiver_id: "456" });
```

##### Server to Client Events

1. **authenticated** - Authentication Success
```javascript
socket.on("authenticated", (data) => {
  console.log("Authentication success:", data.user_id);
});
```

2. **new_message** - New Message Receiving
```javascript
socket.on("new_message", (data) => {
  console.log("New message:", data);
  // {
  //   sender_id: "123",
  //   receiver_id: "456",
  //   content: "안녕하세요",
  //   timestamp: "2024-03-11T12:00:00Z"
  // }
});
```

3. **message_sent** - Message Sending Confirmation
```javascript
socket.on("message_sent", (data) => {
  console.log("Message sending completed:", data);
});
```

4. **user_disconnected** - User Connection Disconnection
```javascript
socket.on("user_disconnected", (data) => {
  console.log("User connection ended:", data.user_id);
});
```

5. **typing** - Typing Status Receiving
```javascript
socket.on("typing", (data) => {
  console.log("User is typing:", data.user_id);
});
```

6. **error** - Error Message
```javascript
socket.on("error", (data) => {
  console.error("Error:", data.message);
});
```

7. **message_read** - Message Read Notification
```javascript
socket.on("message_read", (data) => {
  console.log("Message read:", data);
  // {
  //   message_id: "789",
  //   reader_id: "456",
  //   timestamp: "2024-03-11T12:00:00Z"
  // }
});
```

#### Client-Side Implementation Example
```javascript
import { io } from "socket.io-client";
import { useState, useEffect } from "react";

// Socket.IO connection and message processing
function useChatConnection(userId) {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    // Socket.IO connection creation
    const newSocket = io("http://localhost:8000", {
      path: "/socket.io",
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    
    // Connection events
    newSocket.on("connect", () => {
      console.log("Socket.IO connected");
      // Connection after authentication
      newSocket.emit("authenticate", { user_id: userId });
    });
    
    // Authentication event
    newSocket.on("authenticated", (data) => {
      console.log("Authentication success:", data.user_id);
      setIsConnected(true);
    });
    
    // Message receiving event
    newSocket.on("new_message", (data) => {
      console.log("New message received:", data);
      setMessages(prev => [...prev, data]);
    });
    
    // Message sending confirmation event
    newSocket.on("message_sent", (data) => {
      console.log("Message sending confirmation:", data);
    });
    
    // User connection disconnection event
    newSocket.on("user_disconnected", (data) => {
      console.log("User connection ended:", data.user_id);
    });
    
    // Error event
    newSocket.on("error", (data) => {
      console.error("Socket.IO error:", data.message);
    });
    
    // Connection disconnection event
    newSocket.on("disconnect", (reason) => {
      console.log("Socket.IO disconnection:", reason);
      setIsConnected(false);
    });
    
    setSocket(newSocket);
    
    // Clean up when component unmounts
    return () => {
      newSocket.disconnect();
    };
  }, [userId]);
  
  // Message sending function
  const sendMessage = (receiverId, content) => {
    if (socket && isConnected) {
      socket.emit("message", {
        receiver_id: receiverId,
        content: content,
        timestamp: new Date().toISOString()
      });
    }
  };
  
  // Typing status sending function
  const sendTyping = (receiverId) => {
    if (socket && isConnected) {
      socket.emit("typing", { receiver_id: receiverId });
    }
  };
  
  return { socket, isConnected, messages, sendMessage, sendTyping };
}

// Usage example
function ChatComponent({ userId, contactId }) {
  const { isConnected, messages, sendMessage, sendTyping } = useChatConnection(userId);
  const [inputText, setInputText] = useState("");
  
  const handleSend = () => {
    if (inputText.trim() !== "") {
      sendMessage(contactId, inputText);
      setInputText("");
    }
  };
  
  const handleInputChange = (e) => {
    setInputText(e.target.value);
    sendTyping(contactId);
  };
  
  return (
    <div>
      <div>Connection status: {isConnected ? "Connected" : "Connecting..."}</div>
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={msg.sender_id === userId ? "sent" : "received"}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input 
          type="text" 
          value={inputText} 
          onChange={handleInputChange} 
          disabled={!isConnected} 
        />
        <button onClick={handleSend} disabled={!isConnected}>Send</button>
      </div>
    </div>
  );
}
```

## Development Environment Setup

1. Virtual environment creation and activation
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

2. Dependency installation
```bash
pip install -r requirements.txt
```

3. Server execution
```bash
uvicorn app.main:app --reload
```

## Notes

- The development environment runs on `localhost:8000`.
- For production environments, you need to change to an appropriate host and port.
- Socket.IO connection requires user authentication (authenticate event).
- Messages are stored in the server's queue for offline users, and will be automatically sent when the user comes online.
- Frontend needs to implement reconnection and error handling logic.
- CORS setting is allowed for all sources in the development environment, but it needs to be restricted for production environments. 