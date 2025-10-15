"""
CRUD operations for notifications and notification preferences.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc

from ..shared.models.bot_builder import Notification, NotificationPreference
from ..shared.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationPreferenceUpdate,
    NotificationFilter
)

logger = logging.getLogger(__name__)


def create_notification(db: Session, notification_data: NotificationCreate) -> Notification:
    """Create a new notification."""
    try:
        notification = Notification(
            user_id=notification_data.user_id,
            organization_id=notification_data.organization_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            priority=notification_data.priority
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Created notification {notification.id} for user {notification_data.user_id}")
        return notification
        
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.rollback()
        raise


def get_user_notifications(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 50,
    filter_params: Optional[NotificationFilter] = None
) -> List[Notification]:
    """Get user notifications with optional filtering."""
    try:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if filter_params:
            # Apply filters
            if filter_params.type:
                query = query.filter(Notification.type == filter_params.type)
            
            if filter_params.priority:
                query = query.filter(Notification.priority == filter_params.priority)
            
            if filter_params.is_read is not None:
                query = query.filter(Notification.is_read == filter_params.is_read)
            
            if filter_params.start_date:
                query = query.filter(Notification.created_at >= filter_params.start_date)
            
            if filter_params.end_date:
                query = query.filter(Notification.created_at <= filter_params.end_date)
        
        # Order by created_at descending (newest first)
        query = query.order_by(desc(Notification.created_at))
        
        # Apply pagination
        notifications = query.offset(skip).limit(limit).all()
        
        return notifications
        
    except Exception as e:
        logger.error(f"Failed to get user notifications: {e}")
        return []


def get_unread_count(db: Session, user_id: int) -> int:
    """Get count of unread notifications for a user."""
    try:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to get unread count: {e}")
        return 0


def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
    """Mark a notification as read."""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
            
            logger.info(f"Marked notification {notification_id} as read")
            return notification
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        db.rollback()
        return None


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read for a user."""
    try:
        updated_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        db.commit()
        
        logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
        return updated_count
        
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        db.rollback()
        return 0


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Delete a notification."""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            db.delete(notification)
            db.commit()
            
            logger.info(f"Deleted notification {notification_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        db.rollback()
        return False


def get_user_preferences(db: Session, user_id: int) -> Optional[NotificationPreference]:
    """Get user notification preferences."""
    try:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
            
            logger.info(f"Created default preferences for user {user_id}")
        
        return prefs
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        db.rollback()
        return None


def update_user_preferences(
    db: Session, 
    user_id: int, 
    preferences: NotificationPreferenceUpdate
) -> Optional[NotificationPreference]:
    """Update user notification preferences."""
    try:
        prefs = get_user_preferences(db, user_id)
        if not prefs:
            return None
        
        # Update preferences
        update_data = preferences.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        db.commit()
        db.refresh(prefs)
        
        logger.info(f"Updated notification preferences for user {user_id}")
        return prefs
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        db.rollback()
        return None


def get_notifications_by_type(db: Session, user_id: int, type: str) -> List[Notification]:
    """Get notifications filtered by type."""
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == type
        ).order_by(desc(Notification.created_at)).all()
        
        return notifications
        
    except Exception as e:
        logger.error(f"Failed to get notifications by type: {e}")
        return []


def get_notification_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Get notification summary for a user."""
    try:
        # Get total count
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        
        # Get unread count
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        # Get count by type
        by_type = db.query(
            Notification.type,
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.type).all()
        
        # Get recent notifications (last 10)
        recent = db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(desc(Notification.created_at)).limit(10).all()
        
        return {
            "total": total,
            "unread": unread,
            "by_type": dict(by_type),
            "recent": recent
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification summary: {e}")
        return {"total": 0, "unread": 0, "by_type": {}, "recent": []}


def cleanup_old_notifications(db: Session, days: int = 30) -> int:
    """Delete notifications older than specified days."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {e}")
        db.rollback()
        return 0


def bulk_mark_as_read(db: Session, user_id: int, notification_ids: List[int]) -> int:
    """Mark multiple notifications as read."""
    try:
        updated_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids),
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        db.commit()
        
        logger.info(f"Bulk marked {updated_count} notifications as read for user {user_id}")
        return updated_count
        
    except Exception as e:
        logger.error(f"Failed to bulk mark notifications as read: {e}")
        db.rollback()
        return 0


def bulk_delete_notifications(db: Session, user_id: int, notification_ids: List[int]) -> int:
    """Delete multiple notifications."""
    try:
        deleted_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids)
        ).delete()
        
        db.commit()
        
        logger.info(f"Bulk deleted {deleted_count} notifications for user {user_id}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to bulk delete notifications: {e}")
        db.rollback()
        return 0


def get_notification_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get detailed notification statistics."""
    try:
        # Basic counts
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        # By type
        by_type = db.query(
            Notification.type,
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.type).all()
        
        # By priority
        by_priority = db.query(
            Notification.priority,
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.priority).all()
        
        # Average read time (for read notifications)
        read_notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == True,
            Notification.read_at.isnot(None)
        ).all()
        
        avg_read_time_hours = None
        if read_notifications:
            read_times = []
            for notif in read_notifications:
                if notif.read_at:
                    read_time = (notif.read_at - notif.created_at).total_seconds() / 3600
                    read_times.append(read_time)
            
            if read_times:
                avg_read_time_hours = sum(read_times) / len(read_times)
        
        # Most active day
        most_active_day = db.query(
            func.date(Notification.created_at),
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id
        ).group_by(
            func.date(Notification.created_at)
        ).order_by(
            func.count(Notification.id).desc()
        ).first()
        
        return {
            "total_notifications": total,
            "unread_notifications": unread,
            "notifications_by_type": dict(by_type),
            "notifications_by_priority": dict(by_priority),
            "avg_read_time_hours": avg_read_time_hours,
            "most_active_day": most_active_day[0].isoformat() if most_active_day else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        return {
            "total_notifications": 0,
            "unread_notifications": 0,
            "notifications_by_type": {},
            "notifications_by_priority": {},
            "avg_read_time_hours": None,
            "most_active_day": None
        }


def clear_all_notifications(db: Session, user_id: int) -> int:
    """Clear all notifications for a user."""
    try:
        deleted_count = db.query(Notification).filter(
            Notification.user_id == user_id
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleared all {deleted_count} notifications for user {user_id}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to clear all notifications: {e}")
        db.rollback()
        return 0
