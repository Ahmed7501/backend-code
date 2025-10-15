"""
Notifications module for real-time notifications and WebSocket management.
"""

from .websocket_manager import ConnectionManager, manager
from .service import NotificationService
from .crud import (
    create_notification,
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    delete_notification,
    get_user_preferences,
    update_user_preferences,
    get_notifications_by_type,
    get_notification_summary,
    bulk_mark_as_read,
    bulk_delete_notifications,
    get_notification_stats,
    clear_all_notifications,
    cleanup_old_notifications
)
from .tasks import (
    cleanup_old_notifications_task,
    cleanup_stale_websocket_connections_task,
    send_notification_reminders_task,
    notification_analytics_task,
    test_notification_system_task
)
from .router import router as notifications_router
from .websocket_router import router as websocket_router

__all__ = [
    # WebSocket Management
    "ConnectionManager",
    "manager",
    
    # Notification Service
    "NotificationService",
    
    # CRUD Operations
    "create_notification",
    "get_user_notifications",
    "get_unread_count",
    "mark_as_read",
    "mark_all_as_read",
    "delete_notification",
    "get_user_preferences",
    "update_user_preferences",
    "get_notifications_by_type",
    "get_notification_summary",
    "bulk_mark_as_read",
    "bulk_delete_notifications",
    "get_notification_stats",
    "clear_all_notifications",
    "cleanup_old_notifications",
    
    # Celery Tasks
    "cleanup_old_notifications_task",
    "cleanup_stale_websocket_connections_task",
    "send_notification_reminders_task",
    "notification_analytics_task",
    "test_notification_system_task",
    
    # Routers
    "notifications_router",
    "websocket_router"
]
