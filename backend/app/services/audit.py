"""
Audit log service
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    user: Optional[User],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Log an action to the audit log
    
    Args:
        db: Database session
        user: User who performed the action
        action: Action type (e.g., 'config_change', 'user_create')
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        old_value: Previous value
        new_value: New value
        ip_address: Client IP address
        user_agent: Client user agent
        
    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    # Also log to console for immediate visibility
    user_str = user.username if user else 'system'
    logger.info("AUDIT: %s - %s - %s:%s", user_str, action, resource_type or 'N/A', resource_id or 'N/A')
    
    return audit_log
