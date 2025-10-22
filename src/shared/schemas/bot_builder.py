
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union, Literal

from .flow_engine import (
    SendMessageNodeConfig, WaitNodeConfig, ConditionNodeConfig,
    WebhookActionNodeConfig, SetAttributeNodeConfig
)


class NodeSchema(BaseModel):
    id: Optional[int] = None
    type: Literal["send_message", "wait", "condition", "webhook_action", "set_attribute"] = Field(
        ..., description="Node type"
    )
    config: Union[
        SendMessageNodeConfig,
        WaitNodeConfig,
        ConditionNodeConfig,
        WebhookActionNodeConfig,
        SetAttributeNodeConfig
    ] = Field(..., description="Node configuration")
    
    @field_validator('config', mode='before')
    @classmethod
    def validate_config_structure(cls, v, info):
        """Ensure config matches the node type."""
        if not isinstance(v, dict):
            raise ValueError("config must be a dictionary")
        if not v:
            raise ValueError("config cannot be empty")
        return v
    
    class Config:
        from_attributes = True


class FlowSchema(BaseModel):
    id: Optional[int] = None
    name: str
    bot_id: int
    structure: List[NodeSchema]
    
    class Config:
        from_attributes = True


class BotSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    is_whatsapp_enabled: Optional[bool] = False
    created_by_id: Optional[int] = None
    organization_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    """Schema for creating a template (user input only)."""
    name: str
    structure: List[NodeSchema]
    
    class Config:
        extra = "forbid"  # Reject any extra fields


class TemplateResponse(BaseModel):
    """Schema for template responses (includes all fields)."""
    id: Optional[int] = None
    name: str
    structure: List[NodeSchema]
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Backward compatibility alias
TemplateSchema = TemplateResponse
