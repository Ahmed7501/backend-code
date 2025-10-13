"""
WhatsApp module for ChatBoost backend.
"""

from .router import router
from .service import whatsapp_service
from .crud import *

__all__ = ["router", "whatsapp_service"]
