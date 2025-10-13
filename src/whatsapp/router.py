"""
WhatsApp API router for sending messages and handling webhooks.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..shared.database import get_sync_session
from ..shared.models.bot_builder import Bot
from ..shared.schemas.whatsapp import (
    WhatsAppMessageRequest,
    WhatsAppTemplateMessage,
    WhatsAppTextMessage,
    WhatsAppMediaMessage,
    WhatsAppInteractiveMessage,
    WhatsAppMessageResponse,
    WebhookEvent,
    WebhookVerification,
    WhatsAppMessageHistory
)
from .service import whatsapp_service
from .crud import (
    save_message,
    update_message_status,
    get_bot_messages,
    get_message_by_whatsapp_id,
    save_webhook_event,
    get_bot_by_id,
    get_bot_by_phone_number,
    get_message_count_by_bot
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post("/send/template", response_model=WhatsAppMessageResponse)
async def send_template_message(
    message: WhatsAppTemplateMessage,
    bot_id: int,
    db: Session = Depends(get_sync_session)
):
    """Send a template message via WhatsApp."""
    bot = get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not bot.is_whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp is not enabled for this bot")
    
    try:
        credentials = await whatsapp_service.get_credentials(bot)
        response = await whatsapp_service.send_template_message(credentials, message)
        
        # Save message to database
        whatsapp_message_id = response.get("messages", [{}])[0].get("id")
        if whatsapp_message_id:
            save_message(
                db=db,
                bot_id=bot_id,
                whatsapp_message_id=whatsapp_message_id,
                direction="outbound",
                message_type="template",
                content=message.dict(),
                recipient_phone=message.to,
                status="sent"
            )
        
        return WhatsAppMessageResponse(
            message_id=whatsapp_message_id or "unknown",
            status="sent",
            bot_id=bot_id,
            created_at=response.get("timestamp", 0)
        )
    
    except Exception as e:
        logger.error(f"Failed to send template message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/send/text", response_model=WhatsAppMessageResponse)
async def send_text_message(
    message: WhatsAppTextMessage,
    bot_id: int,
    db: Session = Depends(get_sync_session)
):
    """Send a text message via WhatsApp."""
    bot = get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not bot.is_whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp is not enabled for this bot")
    
    try:
        credentials = await whatsapp_service.get_credentials(bot)
        response = await whatsapp_service.send_text_message(credentials, message)
        
        # Save message to database
        whatsapp_message_id = response.get("messages", [{}])[0].get("id")
        if whatsapp_message_id:
            save_message(
                db=db,
                bot_id=bot_id,
                whatsapp_message_id=whatsapp_message_id,
                direction="outbound",
                message_type="text",
                content=message.dict(),
                recipient_phone=message.to,
                status="sent"
            )
        
        return WhatsAppMessageResponse(
            message_id=whatsapp_message_id or "unknown",
            status="sent",
            bot_id=bot_id,
            created_at=response.get("timestamp", 0)
        )
    
    except Exception as e:
        logger.error(f"Failed to send text message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/send/media", response_model=WhatsAppMessageResponse)
async def send_media_message(
    message: WhatsAppMediaMessage,
    bot_id: int,
    db: Session = Depends(get_sync_session)
):
    """Send a media message via WhatsApp."""
    bot = get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not bot.is_whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp is not enabled for this bot")
    
    try:
        credentials = await whatsapp_service.get_credentials(bot)
        response = await whatsapp_service.send_media_message(credentials, message)
        
        # Save message to database
        whatsapp_message_id = response.get("messages", [{}])[0].get("id")
        if whatsapp_message_id:
            save_message(
                db=db,
                bot_id=bot_id,
                whatsapp_message_id=whatsapp_message_id,
                direction="outbound",
                message_type="media",
                content=message.dict(),
                recipient_phone=message.to,
                status="sent"
            )
        
        return WhatsAppMessageResponse(
            message_id=whatsapp_message_id or "unknown",
            status="sent",
            bot_id=bot_id,
            created_at=response.get("timestamp", 0)
        )
    
    except Exception as e:
        logger.error(f"Failed to send media message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/send/interactive", response_model=WhatsAppMessageResponse)
async def send_interactive_message(
    message: WhatsAppInteractiveMessage,
    bot_id: int,
    db: Session = Depends(get_sync_session)
):
    """Send an interactive message via WhatsApp."""
    bot = get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not bot.is_whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp is not enabled for this bot")
    
    try:
        credentials = await whatsapp_service.get_credentials(bot)
        response = await whatsapp_service.send_interactive_message(credentials, message)
        
        # Save message to database
        whatsapp_message_id = response.get("messages", [{}])[0].get("id")
        if whatsapp_message_id:
            save_message(
                db=db,
                bot_id=bot_id,
                whatsapp_message_id=whatsapp_message_id,
                direction="outbound",
                message_type="interactive",
                content=message.dict(),
                recipient_phone=message.to,
                status="sent"
            )
        
        return WhatsAppMessageResponse(
            message_id=whatsapp_message_id or "unknown",
            status="sent",
            bot_id=bot_id,
            created_at=response.get("timestamp", 0)
        )
    
    except Exception as e:
        logger.error(f"Failed to send interactive message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """Verify WhatsApp webhook."""
    from config.settings import settings
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_sync_session)
):
    """Receive WhatsApp webhook events."""
    try:
        body = await request.json()
        
        # Save webhook event
        save_webhook_event(db, "webhook", body)
        
        # Process webhook events
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "messages":
                    value = change.get("value", {})
                    
                    # Process incoming messages
                    for message in value.get("messages", []):
                        await process_incoming_message(db, message, value)
                    
                    # Process status updates
                    for status in value.get("statuses", []):
                        await process_status_update(db, status)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def process_incoming_message(db: Session, message: dict, value: dict):
    """Process incoming WhatsApp message."""
    try:
        from_number = message.get("from")
        message_id = message.get("id")
        timestamp = message.get("timestamp")
        message_type = message.get("type")
        
        # Find bot by phone number
        bot = get_bot_by_phone_number(db, value.get("metadata", {}).get("phone_number_id"))
        if not bot:
            logger.warning(f"No bot found for phone number: {value.get('metadata', {}).get('phone_number_id')}")
            return
        
        # Extract message content based on type
        content = {}
        if message_type == "text":
            content = {"text": message.get("text", {}).get("body")}
        elif message_type in ["image", "video", "audio", "document"]:
            content = {
                "media": message.get(message_type, {}),
                "caption": message.get(message_type, {}).get("caption")
            }
        elif message_type == "interactive":
            content = {"interactive": message.get("interactive", {})}
        
        # Save incoming message
        save_message(
            db=db,
            bot_id=bot.id,
            whatsapp_message_id=message_id,
            direction="inbound",
            message_type=message_type,
            content=content,
            sender_phone=from_number,
            status="received"
        )
        
        logger.info(f"Processed incoming message {message_id} from {from_number}")
    
    except Exception as e:
        logger.error(f"Error processing incoming message: {str(e)}")


async def process_status_update(db: Session, status: dict):
    """Process message status update."""
    try:
        message_id = status.get("id")
        status_value = status.get("status")
        
        if message_id and status_value:
            update_message_status(db, message_id, status_value)
            logger.info(f"Updated message {message_id} status to {status_value}")
    
    except Exception as e:
        logger.error(f"Error processing status update: {str(e)}")


@router.get("/messages/{bot_id}", response_model=WhatsAppMessageHistory)
async def get_message_history(
    bot_id: int,
    skip: int = 0,
    limit: int = 100,
    direction: Optional[str] = None,
    db: Session = Depends(get_sync_session)
):
    """Get message history for a bot."""
    bot = get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    messages = get_bot_messages(db, bot_id, skip, limit, direction)
    total = get_message_count_by_bot(db, bot_id, direction)
    
    return WhatsAppMessageHistory(
        messages=[msg.__dict__ for msg in messages],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )
