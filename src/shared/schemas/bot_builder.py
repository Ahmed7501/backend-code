
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NodeSchema(BaseModel):
    node_type: str
    content: Dict[str, Any]


class FlowSchema(BaseModel):
    name: str
    bot_id: int
    structure: List[NodeSchema]


class BotSchema(BaseModel):
    name: str
    description: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    is_whatsapp_enabled: Optional[bool] = False


class TemplateSchema(BaseModel):
    name: str
    structure: List[NodeSchema]
