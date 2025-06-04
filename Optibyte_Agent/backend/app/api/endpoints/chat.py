from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.chat_session import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionWithMessages,
    ChatMessageResponse,
    ChatQuery,
    ChatResponse,
    ChatSessionQuery
)
from app.utils.auth import get_current_user
from app.services.ai_agent import ai_agent
import uuid

router = APIRouter()


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat sessions"""
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    
    # Apply date filters
    conditions = []
    if start_date:
        conditions.append(ChatSession.created_at >= start_date)
    if end_date:
        conditions.append(ChatSession.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(ChatSession.updated_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Add message count and last message for each session
    session_responses = []
    for session in sessions:
        # Get message count
        message_count_result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        messages = message_count_result.scalars().all()
        message_count = len(messages)
        
        # Get last message
        last_message = None
        if messages:
            last_msg = max(messages, key=lambda m: m.timestamp)
            last_message = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
        
        session_response = ChatSessionResponse(
            **session.__dict__,
            message_count=message_count,
            last_message=last_message
        )
        session_responses.append(session_response)
    
    return session_responses


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific chat session with messages"""
    # Get session
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    messages_result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp)
    )
    messages = messages_result.scalars().all()
    
    return ChatSessionWithMessages(
        **session.__dict__,
        messages=[ChatMessageResponse(**msg.__dict__) for msg in messages]
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new chat session"""
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=session_data.title or "New Chat"
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionResponse(**session.__dict__)


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    query: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process chat query and get AI response"""
    session_id = query.session_id
    
    # Create new session if not provided
    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            title="AI Chat"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = session.id
    else:
        # Verify session exists and belongs to user
        session_result = await db.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.user_id == current_user.id
                )
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        content=query.message,
        message_type="user"
    )
    db.add(user_message)
    
    try:
        # Process message through AI agent
        ai_response = await ai_agent.process_message(
            message=query.message,
            user_id=current_user.id,
            session_id=session_id,
            context=query.context
        )
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session_id,
            content=ai_response.get("message", ""),
            message_type="assistant",
            metadata=ai_response.get("metadata", {})
        )
        db.add(ai_message)
        
        # Update session timestamp
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return ChatResponse(
            message=ai_response.get("message", ""),
            session_id=session_id,
            message_type="assistant",
            metadata=ai_response.get("metadata", {}),
            suggested_actions=ai_response.get("suggested_actions", [])
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete chat session and all its messages"""
    # Get session
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Delete all messages in session
    messages_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    messages = messages_result.scalars().all()
    
    for message in messages:
        await db.delete(message)
    
    # Delete session
    await db.delete(session)
    await db.commit()
    
    return {"message": "Chat session deleted successfully"}


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update chat session title"""
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.title = title
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return {"message": "Session title updated", "session": session}


@router.get("/messages/{session_id}", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages from a chat session"""
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    messages_result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).offset(offset).limit(limit)
    )
    messages = messages_result.scalars().all()
    
    return [ChatMessageResponse(**msg.__dict__) for msg in messages]


@router.post("/feedback")
async def submit_chat_feedback(
    message_id: int,
    feedback: str,  # "helpful", "not_helpful", "inaccurate"
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback for a chat message"""
    # This could be expanded to store feedback in a separate table
    # For now, we'll just log it
    import structlog
    logger = structlog.get_logger()
    
    logger.info(
        "Chat feedback received",
        message_id=message_id,
        feedback=feedback,
        comment=comment,
        user_id=current_user.id
    )
    
    return {"message": "Feedback submitted successfully"}
