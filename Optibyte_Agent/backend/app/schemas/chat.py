from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageBase(BaseModel):
    """Base chat message schema"""
    content: str
    message_type: str = "user"  # user, assistant, system


class ChatMessageCreate(ChatMessageBase):
    """Chat message creation schema"""
    session_id: Optional[str] = None


class ChatMessageResponse(ChatMessageBase):
    """Chat message response schema"""
    id: int
    session_id: str
    user_id: Optional[int] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    """Base chat session schema"""
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    """Chat session creation schema"""
    pass


class ChatSessionResponse(ChatSessionBase):
    """Chat session response schema"""
    id: str
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = None
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionResponse):
    """Chat session with messages"""
    messages: List[ChatMessageResponse] = []


class ChatQuery(BaseModel):
    """Chat query request"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response"""
    message: str
    session_id: str
    message_type: str = "assistant"
    metadata: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None


class ChatSessionQuery(BaseModel):
    """Chat session query parameters"""
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
