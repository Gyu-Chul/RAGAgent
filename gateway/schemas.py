from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Request Models
class MessageRequest(BaseModel):
    chat_room_id: str
    sender: str
    content: str

class ChatRoomRequest(BaseModel):
    name: str
    repository_id: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    username: str

# Response Models
class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    sender: str
    content: str
    timestamp: datetime
    sources: Optional[List[str]] = None