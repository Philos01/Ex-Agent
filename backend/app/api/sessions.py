"""
Session management API routes
"""
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.session import Session as ChatSession
from app.models.message import Message


BEIJING_TZ = ZoneInfo('Asia/Shanghai')


def format_beijing_time(dt):
    """
    将 datetime 对象转换为北京时间字符串，返回 HH:MM 格式
    """
    if dt is None:
        return None
    try:
        if isinstance(dt, str):
            # 如果已经是字符串，尝试解析为 datetime
            from datetime import datetime
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        # 确保 datetime 对象有时区信息，如果没有则假设是 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # 转换为北京时间
        dt_beijing = dt.astimezone(BEIJING_TZ)
        
        # 格式化为 HH:MM
        return dt_beijing.strftime('%H:%M')
    except Exception as e:
        print(f'[DEBUG] Error formatting time: {e}')
        return None


def safe_isoformat(dt):
    """安全地将 datetime 对象转换为带时区的 ISO 格式字符串（北京时间）"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    try:
        # 确保 datetime 对象有时区信息，如果没有则假设是 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # 转换为北京时间
        dt_beijing = dt.astimezone(BEIJING_TZ)
        
        return dt_beijing.isoformat()
    except Exception as e:
        print(f'[DEBUG] Error converting to ISO format: {e}')
        return None

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionCreate(BaseModel):
    session_name: str


class MessageCreate(BaseModel):
    role: str
    content: str
    sources: Optional[List[dict]] = None


class SessionResponse(BaseModel):
    id: int
    session_name: str
    is_active: bool
    created_at: str
    updated_at: str
    last_message_preview: Optional[str] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[dict]]
    created_at: str

    class Config:
        from_attributes = True


class ContextMessage(BaseModel):
    role: str
    content: str


class SessionContextResponse(BaseModel):
    session_id: int
    context_messages: List[ContextMessage]
    total_messages: int


@router.get("", response_model=List[SessionResponse])
def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of user's active sessions with previews
    """
    sessions = db.query(ChatSession).filter(
        and_(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True
        )
    ).order_by(desc(ChatSession.updated_at)).all()
    
    return [
        SessionResponse(
            id=s.id,
            session_name=s.session_name,
            is_active=s.is_active,
            created_at=safe_isoformat(s.created_at),
            updated_at=safe_isoformat(s.updated_at),
            last_message_preview=s.last_message_preview,
            message_count=s.message_count or 0
        ) for s in sessions
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session
    """
    new_session = ChatSession(
        user_id=current_user.id,
        session_name=session_data.session_name,
        message_count=0
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return SessionResponse(
        id=new_session.id,
        session_name=new_session.session_name,
        is_active=new_session.is_active,
        created_at=safe_isoformat(new_session.created_at),
        updated_at=safe_isoformat(new_session.updated_at),
        last_message_preview=new_session.last_message_preview,
        message_count=new_session.message_count
    )


@router.get("/{session_id}")
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get session details with messages
    """
    session = db.query(ChatSession).filter(
        and_(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get session messages
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).all()
    
    return {
        "session": SessionResponse(
            id=session.id,
            session_name=session.session_name,
            is_active=session.is_active,
            created_at=safe_isoformat(session.created_at),
            updated_at=safe_isoformat(session.updated_at),
            last_message_preview=session.last_message_preview,
            message_count=session.message_count
        ),
        "messages": [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=safe_isoformat(m.created_at)
            ) for m in messages
        ]
    }


@router.get("/{session_id}/context", response_model=SessionContextResponse)
def get_session_context(
    session_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get session context for LLM context injection
    Returns last N messages formatted for LLM input
    """
    session = db.query(ChatSession).filter(
        and_(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get last N messages
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.desc()).limit(limit).all()
    
    # Reverse to get chronological order
    messages = list(reversed(messages))
    
    # Format for LLM context
    context_messages = [
        ContextMessage(role=m.role, content=m.content)
        for m in messages
    ]
    
    return SessionContextResponse(
        session_id=session_id,
        context_messages=context_messages,
        total_messages=session.message_count
    )


@router.post("/{session_id}/messages", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
def add_message(
    session_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a message to a session
    """
    # Verify session ownership
    session = db.query(ChatSession).filter(
        and_(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Create message
    new_message = Message(
        session_id=session_id,
        user_id=current_user.id,
        role=message_data.role,
        content=message_data.content,
        sources=message_data.sources
    )
    
    db.add(new_message)
    
    # Update session metadata
    from sqlalchemy.sql import func
    session.updated_at = func.now()
    session.message_count = (session.message_count or 0) + 1
    # Update preview with the new content (truncate if too long)
    session.last_message_preview = message_data.content[:200]
    
    db.commit()
    db.refresh(new_message)
    
    return MessageResponse(
        id=new_message.id,
        role=new_message.role,
        content=new_message.content,
        sources=new_message.sources,
        created_at=safe_isoformat(new_message.created_at)
    )


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a session (mark as inactive)
    """
    session = db.query(ChatSession).filter(
        and_(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Soft delete
    session.is_active = False
    db.commit()
    
    return {"message": "Session deleted successfully"}
