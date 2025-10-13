"""
WhatsApp CRUD operations for database interactions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..shared.models.bot_builder import Bot, WhatsAppMessage, WhatsAppWebhookEvent


def save_message(
    db: Session,
    bot_id: int,
    whatsapp_message_id: str,
    direction: str,
    message_type: str,
    content: Dict[str, Any],
    recipient_phone: Optional[str] = None,
    sender_phone: Optional[str] = None,
    status: str = "sent"
) -> WhatsAppMessage:
    """Save a WhatsApp message to the database."""
    message = WhatsAppMessage(
        bot_id=bot_id,
        whatsapp_message_id=whatsapp_message_id,
        direction=direction,
        message_type=message_type,
        content=content,
        recipient_phone=recipient_phone,
        sender_phone=sender_phone,
        status=status
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def update_message_status(
    db: Session,
    whatsapp_message_id: str,
    status: str
) -> Optional[WhatsAppMessage]:
    """Update the status of a WhatsApp message."""
    message = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.whatsapp_message_id == whatsapp_message_id
    ).first()
    
    if message:
        message.status = status
        message.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
    
    return message


def get_bot_messages(
    db: Session,
    bot_id: int,
    skip: int = 0,
    limit: int = 100,
    direction: Optional[str] = None
) -> List[WhatsAppMessage]:
    """Get message history for a specific bot."""
    query = db.query(WhatsAppMessage).filter(WhatsAppMessage.bot_id == bot_id)
    
    if direction:
        query = query.filter(WhatsAppMessage.direction == direction)
    
    return query.order_by(desc(WhatsAppMessage.created_at)).offset(skip).limit(limit).all()


def get_message_by_whatsapp_id(
    db: Session,
    whatsapp_message_id: str
) -> Optional[WhatsAppMessage]:
    """Get a message by its WhatsApp message ID."""
    return db.query(WhatsAppMessage).filter(
        WhatsAppMessage.whatsapp_message_id == whatsapp_message_id
    ).first()


def save_webhook_event(
    db: Session,
    event_type: str,
    payload: Dict[str, Any]
) -> WhatsAppWebhookEvent:
    """Save a webhook event to the database."""
    event = WhatsAppWebhookEvent(
        event_type=event_type,
        payload=payload
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_unprocessed_webhook_events(
    db: Session,
    limit: int = 100
) -> List[WhatsAppWebhookEvent]:
    """Get unprocessed webhook events."""
    return db.query(WhatsAppWebhookEvent).filter(
        WhatsAppWebhookEvent.processed == False
    ).order_by(WhatsAppWebhookEvent.created_at).limit(limit).all()


def mark_webhook_event_processed(
    db: Session,
    event_id: int
) -> Optional[WhatsAppWebhookEvent]:
    """Mark a webhook event as processed."""
    event = db.query(WhatsAppWebhookEvent).filter(
        WhatsAppWebhookEvent.id == event_id
    ).first()
    
    if event:
        event.processed = True
        db.commit()
        db.refresh(event)
    
    return event


def get_bot_by_id(db: Session, bot_id: int) -> Optional[Bot]:
    """Get a bot by ID."""
    return db.query(Bot).filter(Bot.id == bot_id).first()


def get_bot_by_phone_number(
    db: Session,
    phone_number: str
) -> Optional[Bot]:
    """Get a bot by WhatsApp phone number."""
    return db.query(Bot).filter(
        Bot.whatsapp_phone_number_id == phone_number,
        Bot.is_whatsapp_enabled == True
    ).first()


def get_message_count_by_bot(
    db: Session,
    bot_id: int,
    direction: Optional[str] = None
) -> int:
    """Get message count for a bot."""
    query = db.query(WhatsAppMessage).filter(WhatsAppMessage.bot_id == bot_id)
    
    if direction:
        query = query.filter(WhatsAppMessage.direction == direction)
    
    return query.count()
