"""
Pydantic schemas for notifications and real-time updates.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationSchema(BaseModel):
    """Schema for notification data."""
    id: Optional[int] = None
    user_id: int
    organization_id: int
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    priority: str = "normal"
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
       from_attributes = True


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    user_id: int
    organization_id: int
    type: str = Field(..., pattern="^(message_status|flow_event|system|mention)$")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    data: Optional[Dict[str, Any]] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationPreferenceSchema(BaseModel):
    """Schema for notification preferences."""
    id: Optional[int] = None
    user_id: int
    email_enabled: bool = True
    push_enabled: bool = True
    message_status_enabled: bool = True
    flow_events_enabled: bool = True
    system_notifications_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
       from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    message_status_enabled: Optional[bool] = None
    flow_events_enabled: Optional[bool] = None
    system_notifications_enabled: Optional[bool] = None


class NotificationSummary(BaseModel):
    """Schema for notification summary."""
    total: int
    unread: int
    by_type: Dict[str, int]
    recent: List[NotificationSchema]


class NotificationCount(BaseModel):
    """Schema for notification count."""
    total: int
    unread: int
    by_type: Dict[str, int]


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str = Field(..., pattern="^(notification|status_update|ping|pong|connected|mark_read)$")
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class WebSocketConnection(BaseModel):
    """Schema for WebSocket connection info."""
    user_id: int
    organization_id: int
    connected_at: datetime
    is_active: bool


class NotificationFilter(BaseModel):
    """Schema for filtering notifications."""
    type: Optional[str] = None
    priority: Optional[str] = None
    is_read: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BulkNotificationAction(BaseModel):
    """Schema for bulk notification actions."""
    action: str = Field(..., pattern="^(mark_read|mark_unread|delete)$")
    notification_ids: List[int] = Field(..., min_items=1)


class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    avg_read_time_hours: Optional[float] = None
    most_active_day: Optional[str] = None


class NotificationTemplate(BaseModel):
    """Schema for notification templates."""
    id: Optional[int] = None
    name: str
    type: str
    title_template: str
    message_template: str
    variables: List[str] = []
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
       from_attributes = True


class NotificationTemplateCreate(BaseModel):
    """Schema for creating notification templates."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(message_status|flow_event|system|mention)$")
    title_template: str = Field(..., min_length=1, max_length=200)
    message_template: str = Field(..., min_length=1, max_length=1000)
    variables: List[str] = []


class NotificationDeliveryStatus(BaseModel):
    """Schema for notification delivery status."""
    notification_id: int
    delivery_method: str = Field(..., pattern="^(websocket|email|push)$")
    status: str = Field(..., pattern="^(pending|sent|delivered|failed)$")
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
