"""
WhatsApp API service layer for sending and receiving messages.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from config.settings import settings
from ..shared.models.bot_builder import Bot
from ..shared.schemas.whatsapp import (
    WhatsAppTemplateRequest,
    WhatsAppTemplateMessage,
    WhatsAppTextMessage,
    WhatsAppMediaMessage,
    WhatsAppInteractiveMessage,
    WhatsAppCredentials
)

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for WhatsApp API integration."""
    
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
    
    async def get_credentials(self, bot: Bot) -> WhatsAppCredentials:
        """Get WhatsApp credentials for a bot (bot-specific or default)."""
        return WhatsAppCredentials(
            access_token=bot.whatsapp_access_token or settings.WHATSAPP_ACCESS_TOKEN,
            phone_number_id=bot.whatsapp_phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID,
            business_account_id=bot.whatsapp_business_account_id or settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        )
    
    async def send_template_message(
        self,
        credentials: WhatsAppCredentials,
        message: WhatsAppTemplateRequest
    ) -> Dict[str, Any]:
        """Send a template message via WhatsApp API with comprehensive logging."""
        from fastapi import HTTPException
        
        # Validate credentials
        if not credentials.access_token or not credentials.phone_number_id:
            logger.error("Missing WhatsApp credentials")
            raise HTTPException(
                status_code=500,
                detail="WhatsApp credentials missing for bot"
            )
        
        url = f"{self.base_url}/{credentials.phone_number_id}/messages"
        
        # Build payload with variables
        payload = {
            "messaging_product": "whatsapp",
            "to": message.to,
            "type": "template",
            "template": {
                "name": message.template_name,
                "language": {"code": "en_US"}
            }
        }
        
        if message.variables:
            payload["template"]["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": var} for var in message.variables]
            }]
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Sending WhatsApp template to {message.to}: {message.template_name}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                # Log response details
                logger.debug(f"WhatsApp API response: status={response.status_code}, body={response.text[:200]}")
                
                # Check for errors
                if response.status_code >= 400:
                    error_detail = f"Upstream WhatsApp API error: {response.text[:200]}"
                    logger.error(error_detail)
                    raise HTTPException(status_code=502, detail=error_detail)
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Upstream error: {str(e.response.text)[:200]}"
                logger.error(f"WhatsApp API HTTP error: {error_msg}")
                raise HTTPException(status_code=502, detail=error_msg)
            except httpx.RequestError as e:
                error_msg = f"Network error contacting WhatsApp API: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(status_code=503, detail=error_msg)
    
    async def send_text_message(
        self,
        credentials: WhatsAppCredentials,
        message: WhatsAppTextMessage
    ) -> Dict[str, Any]:
        """Send a text message via WhatsApp API."""
        url = f"{self.base_url}/{credentials.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": message.to,
            "type": "text",
            "text": {"body": message.text}
        }
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def send_media_message(
        self,
        credentials: WhatsAppCredentials,
        message: WhatsAppMediaMessage
    ) -> Dict[str, Any]:
        """Send a media message via WhatsApp API."""
        url = f"{self.base_url}/{credentials.phone_number_id}/messages"
        
        media_data = {}
        if message.media_url:
            media_data["link"] = message.media_url
        elif message.media_id:
            media_data["id"] = message.media_id
        
        payload = {
            "messaging_product": "whatsapp",
            "to": message.to,
            "type": message.media_type,
            message.media_type: media_data
        }
        
        if message.caption:
            payload[message.media_type]["caption"] = message.caption
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def send_interactive_message(
        self,
        credentials: WhatsAppCredentials,
        message: WhatsAppInteractiveMessage
    ) -> Dict[str, Any]:
        """Send an interactive message via WhatsApp API."""
        url = f"{self.base_url}/{credentials.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": message.to,
            "type": "interactive",
            "interactive": {
                "type": message.interactive_type,
                "body": message.body,
                "action": message.action
            }
        }
        
        if message.header:
            payload["interactive"]["header"] = message.header
        
        if message.footer:
            payload["interactive"]["footer"] = message.footer
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def mark_message_as_read(
        self,
        credentials: WhatsAppCredentials,
        message_id: str
    ) -> Dict[str, Any]:
        """Mark a message as read."""
        url = f"{self.base_url}/{credentials.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def upload_media(
        self,
        credentials: WhatsAppCredentials,
        media_url: str,
        media_type: str
    ) -> Dict[str, Any]:
        """Upload media to WhatsApp."""
        url = f"{self.base_url}/{credentials.phone_number_id}/media"
        
        payload = {
            "messaging_product": "whatsapp",
            "url": media_url,
            "type": media_type
        }
        
        headers = {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


# Global service instance
whatsapp_service = WhatsAppService()
