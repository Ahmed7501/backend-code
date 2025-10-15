"""
Celery tasks for notifications cleanup and maintenance.
"""

import logging
from celery import Celery
from datetime import datetime, timedelta

from ..flow_engine.celery_app import celery_app
from ..shared.database import SessionLocal
from .crud import cleanup_old_notifications

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_old_notifications")
def cleanup_old_notifications_task(days: int = 30):
    """Delete notifications older than specified days."""
    try:
        db = SessionLocal()
        try:
            deleted_count = cleanup_old_notifications(db, days)
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return {"deleted": deleted_count, "days": days}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {e}")
        return {"error": str(e)}


@celery_app.task(name="cleanup_stale_websocket_connections")
def cleanup_stale_websocket_connections_task():
    """Clean up stale WebSocket connections."""
    try:
        from .websocket_manager import manager
        manager.cleanup_stale_connections()
        logger.info("Cleaned up stale WebSocket connections")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to cleanup stale WebSocket connections: {e}")
        return {"error": str(e)}


@celery_app.task(name="send_notification_reminders")
def send_notification_reminders_task():
    """Send reminders for unread notifications older than 24 hours."""
    try:
        db = SessionLocal()
        try:
            from ..shared.models.bot_builder import Notification
            from .service import NotificationService
            
            # Get unread notifications older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            old_unread_notifications = db.query(Notification).filter(
                Notification.is_read == False,
                Notification.created_at < cutoff_time
            ).all()
            
            notification_service = NotificationService(db)
            reminder_count = 0
            
            for notification in old_unread_notifications:
                # Send reminder notification
                notification_service.create_notification(
                    user_id=notification.user_id,
                    organization_id=notification.organization_id,
                    type="system",
                    title="Unread Notification Reminder",
                    message=f"You have {len(old_unread_notifications)} unread notifications",
                    data={
                        "reminder": True,
                        "original_notification_id": notification.id
                    },
                    priority="normal"
                )
                reminder_count += 1
            
            logger.info(f"Sent {reminder_count} notification reminders")
            return {"reminders_sent": reminder_count}
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to send notification reminders: {e}")
        return {"error": str(e)}


@celery_app.task(name="notification_analytics")
def notification_analytics_task():
    """Generate notification analytics and statistics."""
    try:
        db = SessionLocal()
        try:
            from ..shared.models.bot_builder import Notification
            from sqlalchemy import func
            
            # Get basic statistics
            total_notifications = db.query(Notification).count()
            unread_notifications = db.query(Notification).filter(
                Notification.is_read == False
            ).count()
            
            # Get notifications by type
            by_type = db.query(
                Notification.type,
                func.count(Notification.id)
            ).group_by(Notification.type).all()
            
            # Get notifications by priority
            by_priority = db.query(
                Notification.priority,
                func.count(Notification.id)
            ).group_by(Notification.priority).all()
            
            # Get daily notification counts for the last 7 days
            daily_counts = []
            for i in range(7):
                date = datetime.utcnow().date() - timedelta(days=i)
                count = db.query(Notification).filter(
                    func.date(Notification.created_at) == date
                ).count()
                daily_counts.append({"date": date.isoformat(), "count": count})
            
            analytics = {
                "total_notifications": total_notifications,
                "unread_notifications": unread_notifications,
                "notifications_by_type": dict(by_type),
                "notifications_by_priority": dict(by_priority),
                "daily_counts": daily_counts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Generated notification analytics: {analytics}")
            return analytics
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to generate notification analytics: {e}")
        return {"error": str(e)}


@celery_app.task(name="test_notification_system")
def test_notification_system_task():
    """Test the notification system by creating test notifications."""
    try:
        db = SessionLocal()
        try:
            from ..shared.models.auth import User, OrganizationMember
            from .service import NotificationService
            
            # Get a random user with organization
            user = db.query(User).join(OrganizationMember).filter(
                User.organization_id.isnot(None)
            ).first()
            
            if not user:
                logger.warning("No users with organizations found for testing")
                return {"error": "No test users available"}
            
            notification_service = NotificationService(db)
            
            # Create test notifications
            test_notifications = [
                {
                    "type": "system",
                    "title": "System Test Notification",
                    "message": "This is a test notification from the system",
                    "priority": "normal"
                },
                {
                    "type": "message_status",
                    "title": "Message Delivered",
                    "message": "Test message to +1234567890 has been delivered",
                    "priority": "normal"
                },
                {
                    "type": "flow_event",
                    "title": "Flow Completed",
                    "message": "Test flow execution has completed successfully",
                    "priority": "normal"
                }
            ]
            
            created_count = 0
            for notif_data in test_notifications:
                notification_service.create_notification(
                    user_id=user.id,
                    organization_id=user.organization_id,
                    **notif_data
                )
                created_count += 1
            
            logger.info(f"Created {created_count} test notifications for user {user.id}")
            return {
                "test_notifications_created": created_count,
                "test_user_id": user.id,
                "test_organization_id": user.organization_id
            }
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to test notification system: {e}")
        return {"error": str(e)}
