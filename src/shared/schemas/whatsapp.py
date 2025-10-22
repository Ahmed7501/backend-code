"""
WhatsApp API schemas for message handling and webhook events.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class WhatsAppCredentials(BaseModel):
    """WhatsApp API credentials."""
    access_token: str
    phone_number_id: str
    business_account_id: Optional[str] = None


class WhatsAppTemplateRequest(BaseModel):
    """Simplified template message request schema."""
    template_name: str = Field(..., description="Template name")
    to: str = Field(..., description="Recipient phone number with country code")
    variables: List[str] = Field(default_factory=list, description="Template variable values")
    
    class Config:
        extra = "forbid"  # Reject unknown fields


class WhatsAppTemplateMessage(BaseModel):
    """Template message schema (deprecated - use WhatsAppTemplateRequest)."""
    to: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Template name")
    language_code: str = Field(default="en_US", description="Language code")
    parameters: Optional[List[str]] = Field(default=None, description="Template parameters")


class WhatsAppTextMessage(BaseModel):
    """Text message schema."""
    to: str = Field(..., description="Recipient phone number")
    text: str = Field(..., description="Message text")


class WhatsAppMediaMessage(BaseModel):
    """Media message schema."""
    to: str = Field(..., description="Recipient phone number")
    media_type: str = Field(..., description="Type: image, video, audio, document")
    media_url: Optional[str] = Field(default=None, description="Media URL")
    media_id: Optional[str] = Field(default=None, description="Media ID from WhatsApp")
    caption: Optional[str] = Field(default=None, description="Media caption")


class WhatsAppButton(BaseModel):
    """WhatsApp button schema."""
    type: str = Field(default="reply", description="Button type")
    reply: Dict[str, str] = Field(..., description="Button reply data")


class WhatsAppInteractiveMessage(BaseModel):
    """Interactive message schema."""
    to: str = Field(..., description="Recipient phone number")
    interactive_type: str = Field(..., description="Type: button, list")
    header: Optional[Dict[str, Any]] = Field(default=None, description="Message header")
    body: Dict[str, str] = Field(..., description="Message body")
    footer: Optional[Dict[str, str]] = Field(default=None, description="Message footer")
    action: Dict[str, Any] = Field(..., description="Interactive action")


class WhatsAppMessageRequest(BaseModel):
    """Generic WhatsApp message request."""
    bot_id: int = Field(..., description="Bot ID")
    message: Union[WhatsAppTemplateMessage, WhatsAppTextMessage, WhatsAppMediaMessage, WhatsAppInteractiveMessage]


class WhatsAppMessageResponse(BaseModel):
    """WhatsApp message response."""
    message_id: str
    status: str
    bot_id: int
    created_at: datetime


class WhatsAppWebhookValue(BaseModel):
    """WhatsApp webhook value containing messages and statuses."""
    messaging_product: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None


class WhatsAppWebhookChange(BaseModel):
    """WhatsApp webhook change entry."""
    field: str
    value: WhatsAppWebhookValue


class WhatsAppWebhookEntry(BaseModel):
    """WhatsApp webhook entry."""
    id: str
    changes: List[WhatsAppWebhookChange]


class WhatsAppWebhookPayload(BaseModel):
    """Complete WhatsApp webhook payload."""
    object: str
    entry: List[WhatsAppWebhookEntry]


class WebhookEvent(BaseModel):
    """WhatsApp webhook event (deprecated - use WhatsAppWebhookPayload)."""
    object: str
    entry: List[Dict[str, Any]]


class MessageStatus(BaseModel):
    """Message status update."""
    message_id: str
    status: str  # sent, delivered, read, failed
    timestamp: datetime
    recipient_id: Optional[str] = None


class IncomingMessage(BaseModel):
    """Incoming WhatsApp message."""
    message_id: str
    from_number: str
    timestamp: datetime
    message_type: str
    content: Dict[str, Any]


class WhatsAppMessageHistory(BaseModel):
    """WhatsApp message history response."""
    messages: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int


class WebhookVerification(BaseModel):
    """Webhook verification request."""
    hub_mode: str
    hub_challenge: str
    hub_verify_token: str
