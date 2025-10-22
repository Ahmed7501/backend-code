"""
REST API router for notifications and notification preferences.
"""

import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..shared.database import get_sync_session
from ..shared.models.auth import User
from ..shared.schemas.notification import (
    NotificationSchema,
    NotificationCreate,
    NotificationUpdate,
    NotificationPreferenceSchema,
    NotificationPreferenceUpdate,
    NotificationSummary,
    NotificationCount,
    NotificationFilter,
    BulkNotificationAction,
    NotificationStats
)
from ..auth.auth import get_current_active_user
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
    clear_all_notifications
)
from .service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationSchema])
async def get_notifications_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get user notifications with optional filtering."""
    try:
        # Create filter object
        filter_params = NotificationFilter(
            type=type,
            priority=priority,
            is_read=is_read,
            limit=limit,
            offset=skip
        )
        
        notifications = await asyncio.to_thread(get_user_notifications, db, current_user.id, skip, limit, filter_params)
        return [NotificationSchema.from_orm(notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.get("/unread", response_model=List[NotificationSchema])
async def get_unread_notifications_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get unread notifications for the current user."""
    try:
        filter_params = NotificationFilter(is_read=False, limit=limit, offset=skip)
        notifications = await asyncio.to_thread(get_user_notifications, db, current_user.id, skip, limit, filter_params)
        return [NotificationSchema.from_orm(notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Failed to get unread notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread notifications"
        )


@router.get("/count", response_model=NotificationCount)
async def get_notification_count_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get notification count for the current user."""
    try:
        total = len(await asyncio.to_thread(get_user_notifications, db, current_user.id, 0, 1000))
        unread = await asyncio.to_thread(get_unread_count, db, current_user.id)
        
        # Get count by type
        notifications = await asyncio.to_thread(get_user_notifications, db, current_user.id, 0, 1000)
        by_type = {}
        for notification in notifications:
            by_type[notification.type] = by_type.get(notification.type, 0) + 1
        
        return NotificationCount(
            total=total,
            unread=unread,
            by_type=by_type
        )
        
    except Exception as e:
        logger.error(f"Failed to get notification count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification count"
        )


@router.put("/{notification_id}/read", response_model=NotificationSchema)
async def mark_notification_read_endpoint(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Mark a notification as read."""
    try:
        notification = await asyncio.to_thread(mark_as_read, db, notification_id, current_user.id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return NotificationSchema.from_orm(notification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.put("/read-all")
async def mark_all_read_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Mark all notifications as read for the current user."""
    try:
        updated_count = await asyncio.to_thread(mark_all_as_read, db, current_user.id)
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.delete("/{notification_id}")
async def delete_notification_endpoint(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Delete a notification."""
    try:
        success = await asyncio.to_thread(delete_notification, db, notification_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.get("/preferences", response_model=NotificationPreferenceSchema)
async def get_notification_preferences_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get notification preferences for the current user."""
    try:
        preferences = await asyncio.to_thread(get_user_preferences, db, current_user.id)
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get preferences"
            )
        
        return NotificationPreferenceSchema.from_orm(preferences)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/preferences", response_model=NotificationPreferenceSchema)
async def update_notification_preferences_endpoint(
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Update notification preferences for the current user."""
    try:
        updated_preferences = await asyncio.to_thread(update_user_preferences, db, current_user.id, preferences)
        if not updated_preferences:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        return NotificationPreferenceSchema.from_orm(updated_preferences)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get notification summary for the current user."""
    try:
        summary = await asyncio.to_thread(get_notification_summary, db, current_user.id)
        
        return NotificationSummary(
            total=summary["total"],
            unread=summary["unread"],
            by_type=summary["by_type"],
            recent=[NotificationSchema.from_orm(n) for n in summary["recent"]]
        )
        
    except Exception as e:
        logger.error(f"Failed to get notification summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification summary"
        )


@router.post("/bulk-action")
async def bulk_notification_action_endpoint(
    action: BulkNotificationAction,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Perform bulk action on notifications."""
    try:
        if action.action == "mark_read":
            updated_count = bulk_mark_as_read(db, current_user.id, action.notification_ids)
            return {
                "message": f"Marked {updated_count} notifications as read",
                "updated_count": updated_count
            }
        elif action.action == "delete":
            deleted_count = bulk_delete_notifications(db, current_user.id, action.notification_ids)
            return {
                "message": f"Deleted {deleted_count} notifications",
                "deleted_count": deleted_count
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {action.action}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )


@router.delete("/clear")
async def clear_all_notifications_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Clear all notifications for the current user."""
    try:
        deleted_count = clear_all_notifications(db, current_user.id)
        
        return {
            "message": f"Cleared {deleted_count} notifications",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear all notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear all notifications"
        )


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get detailed notification statistics for the current user."""
    try:
        stats = get_notification_stats(db, current_user.id)
        
        return NotificationStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification stats"
        )


@router.get("/by-type/{type}", response_model=List[NotificationSchema])
async def get_notifications_by_type_endpoint(
    type: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Get notifications filtered by type."""
    try:
        notifications = get_notifications_by_type(db, current_user.id, type)
        return [NotificationSchema.from_orm(notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Failed to get notifications by type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications by type"
        )


@router.post("/test")
async def test_notification_endpoint(
    title: str = Query(..., description="Test notification title"),
    message: str = Query(..., description="Test notification message"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """Create a test notification for the current user."""
    try:
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to an organization"
            )
        
        notification_service = NotificationService(db)
        notification = await notification_service.create_notification(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            type="system",
            title=title,
            message=message,
            data={"test": True},
            priority="normal"
        )
        
        return {
            "message": "Test notification created successfully",
            "notification_id": notification.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test notification"
        )
