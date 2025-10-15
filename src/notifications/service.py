"""
Notification service for creating and managing notifications.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..shared.models.bot_builder import (
    Notification, 
    NotificationPreference, 
    WhatsAppMessage, 
    Bot, 
    FlowExecution
)
from ..shared.models.auth import OrganizationMember
from .websocket_manager import manager

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and real-time updates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(
        self,
        user_id: int,
        organization_id: int,
        type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: str = "normal"
    ) -> Notification:
        """Create and optionally send notification."""
        try:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                type=type,
                title=title,
                message=message,
                data=data,
                priority=priority
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # Send via WebSocket if user is connected
            await self.send_realtime_notification(notification)
            
            logger.info(f"Created notification {notification.id} for user {user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            self.db.rollback()
            raise
    
    async def send_realtime_notification(self, notification: Notification):
        """Send notification via WebSocket."""
        try:
            message = {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "type": notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "priority": notification.priority,
                    "created_at": notification.created_at.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_to_user(notification.user_id, message)
            
        except Exception as e:
            logger.error(f"Failed to send realtime notification: {e}")
    
    async def notify_message_status_change(
        self,
        message: WhatsAppMessage,
        old_status: str,
        new_status: str
    ):
        """Notify about message status change."""
        try:
            # Get bot and organization
            bot = self.db.query(Bot).filter(Bot.id == message.bot_id).first()
            if not bot:
                logger.warning(f"No bot found for message {message.id}")
                return
            
            # Get organization members who should be notified
            members = self.db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == bot.organization_id
            ).all()
            
            for member in members:
                # Check user preferences
                prefs = self.get_user_preferences(member.user_id)
                if prefs and prefs.message_status_enabled:
                    await self.create_notification(
                        user_id=member.user_id,
                        organization_id=bot.organization_id,
                        type="message_status",
                        title=f"Message {new_status}",
                        message=f"Message to {message.recipient_phone} is now {new_status}",
                        data={
                            "message_id": message.id,
                            "whatsapp_message_id": message.whatsapp_message_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "recipient": message.recipient_phone,
                            "bot_id": bot.id,
                            "bot_name": bot.name
                        },
                        priority="normal" if new_status in ["delivered", "read"] else "high"
                    )
            
            logger.info(f"Notified organization {bot.organization_id} about message status change")
            
        except Exception as e:
            logger.error(f"Failed to notify message status change: {e}")
    
    async def notify_flow_event(
        self,
        execution: FlowExecution,
        event_type: str,
        details: Optional[Dict] = None
    ):
        """Notify about flow execution event."""
        try:
            bot = self.db.query(Bot).filter(Bot.id == execution.bot_id).first()
            if not bot:
                logger.warning(f"No bot found for execution {execution.id}")
                return
            
            members = self.db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == bot.organization_id
            ).all()
            
            for member in members:
                prefs = self.get_user_preferences(member.user_id)
                if prefs and prefs.flow_events_enabled:
                    # Determine priority based on event type
                    priority = "high" if event_type in ["failed", "error"] else "normal"
                    
                    await self.create_notification(
                        user_id=member.user_id,
                        organization_id=bot.organization_id,
                        type="flow_event",
                        title=f"Flow {event_type}",
                        message=f"Flow execution {execution.id} {event_type}",
                        data={
                            "execution_id": execution.id,
                            "flow_id": execution.flow_id,
                            "event_type": event_type,
                            "details": details,
                            "bot_id": bot.id,
                            "bot_name": bot.name,
                            "contact_phone": execution.contact.phone_number if execution.contact else None
                        },
                        priority=priority
                    )
            
            logger.info(f"Notified organization {bot.organization_id} about flow event: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to notify flow event: {e}")
    
    async def notify_system_event(
        self,
        organization_id: int,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: str = "normal"
    ):
        """Notify about system events."""
        try:
            members = self.db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == organization_id
            ).all()
            
            for member in members:
                prefs = self.get_user_preferences(member.user_id)
                if prefs and prefs.system_notifications_enabled:
                    await self.create_notification(
                        user_id=member.user_id,
                        organization_id=organization_id,
                        type="system",
                        title=title,
                        message=message,
                        data=data,
                        priority=priority
                    )
            
            logger.info(f"Notified organization {organization_id} about system event: {title}")
            
        except Exception as e:
            logger.error(f"Failed to notify system event: {e}")
    
    async def notify_user_mention(
        self,
        user_id: int,
        organization_id: int,
        mentioned_by_user_id: int,
        context: str,
        data: Optional[Dict] = None
    ):
        """Notify about user mentions."""
        try:
            # Get mentioning user info
            from ..shared.models.auth import User
            mentioning_user = self.db.query(User).filter(User.id == mentioned_by_user_id).first()
            if not mentioning_user:
                return
            
            await self.create_notification(
                user_id=user_id,
                organization_id=organization_id,
                type="mention",
                title=f"You were mentioned by {mentioning_user.username}",
                message=f"{mentioning_user.username} mentioned you: {context}",
                data={
                    "mentioned_by_user_id": mentioned_by_user_id,
                    "mentioned_by_username": mentioning_user.username,
                    "context": context,
                    **(data or {})
                },
                priority="high"
            )
            
            logger.info(f"Notified user {user_id} about mention from {mentioned_by_user_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify user mention: {e}")
    
    def get_user_preferences(self, user_id: int) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        try:
            prefs = self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).first()
            
            if not prefs:
                # Create default preferences
                prefs = NotificationPreference(user_id=user_id)
                self.db.add(prefs)
                self.db.commit()
                self.db.refresh(prefs)
            
            return prefs
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    def update_user_preferences(
        self, 
        user_id: int, 
        preferences: Dict[str, bool]
    ) -> Optional[NotificationPreference]:
        """Update user notification preferences."""
        try:
            prefs = self.get_user_preferences(user_id)
            if not prefs:
                return None
            
            # Update preferences
            for key, value in preferences.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            self.db.commit()
            self.db.refresh(prefs)
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return prefs
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            self.db.rollback()
            return None
    
    async def broadcast_organization_announcement(
        self,
        organization_id: int,
        title: str,
        message: str,
        priority: str = "normal"
    ):
        """Broadcast announcement to all organization members."""
        try:
            members = self.db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == organization_id
            ).all()
            
            for member in members:
                await self.create_notification(
                    user_id=member.user_id,
                    organization_id=organization_id,
                    type="system",
                    title=title,
                    message=message,
                    priority=priority
                )
            
            logger.info(f"Broadcasted announcement to organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast announcement: {e}")
    
    async def send_connection_status_update(self, user_id: int, status: str):
        """Send connection status update to user."""
        try:
            message = {
                "type": "status_update",
                "data": {
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_to_user(user_id, message)
            
        except Exception as e:
            logger.error(f"Failed to send connection status update: {e}")
    
    def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        try:
            # Get total notifications
            total = self.db.query(Notification).filter(
                Notification.user_id == user_id
            ).count()
            
            # Get unread notifications
            unread = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).count()
            
            # Get notifications by type
            from sqlalchemy import func
            by_type = self.db.query(
                Notification.type,
                func.count(Notification.id)
            ).filter(
                Notification.user_id == user_id
            ).group_by(Notification.type).all()
            
            return {
                "total": total,
                "unread": unread,
                "by_type": dict(by_type)
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            return {"total": 0, "unread": 0, "by_type": {}}
