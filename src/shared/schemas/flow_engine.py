"""
Flow Engine schemas for contact management and flow execution.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum


class ContactSchema(BaseModel):
    """Contact schema for CRUD operations."""
    phone_number: str = Field(..., description="Contact phone number")
    first_name: Optional[str] = Field(None, description="Contact first name")
    last_name: Optional[str] = Field(None, description="Contact last name")
    meta_data: Optional[Dict[str, Any]] = Field(default={}, description="Custom contact fields")


class ContactResponse(BaseModel):
    """Contact response schema."""
    id: int
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
    meta_data: Dict[str, Any]
    attributes: Optional[Dict[str, Any]] = None  # key-value pairs
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # Convert SQLAlchemy InstrumentedList to dict if needed
        attributes_dict = None
        if hasattr(obj, "attributes") and obj.attributes is not None:
            try:
                attributes_dict = {item.key: item.value for item in obj.attributes}  # convert list to dict
            except Exception:
                # fallback if attributes already a dict
                attributes_dict = obj.attributes
        obj_dict = obj.__dict__.copy()
        obj_dict['attributes'] = attributes_dict
        return super().model_validate(obj_dict)


class FlowExecutionStatus(str, Enum):
    """Flow execution status enum."""
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class FlowExecutionSchema(BaseModel):
    """Flow execution schema."""
    flow_id: int = Field(..., description="Flow ID to execute")
    contact_phone: str = Field(..., description="Contact phone number")
    bot_id: int = Field(..., description="Bot ID")
    initial_state: Optional[Dict[str, Any]] = Field(default={}, description="Initial execution state")


class FlowExecutionResponse(BaseModel):
    """Flow execution response schema."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    flow_id: int
    contact_id: int
    bot_id: int
    current_node_index: int
    state: Dict[str, Any]
    status: FlowExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    last_executed_at: datetime


class NodeExecutionResult(BaseModel):
    """Result of node execution."""
    success: bool
    next_node_index: Optional[int] = None
    scheduled_task_id: Optional[str] = None
    error: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class SendMessageNodeConfig(BaseModel):
    """Configuration for send_message nodes."""
    message_type: Literal["text", "template", "media", "interactive"] = Field(..., description="Message type")
    content: Dict[str, Any] = Field(..., description="Message content", min_length=1)
    variables: Optional[List[str]] = Field(default_factory=list, description="Variables to interpolate")
    # If missing or null, default to -1 which we treat as end-of-flow
    next: int = Field(default=-1, description="Next node index; -1 means end-of-flow")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v:
            raise ValueError("content cannot be empty")
        return v
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        allowed = {"text", "template", "media", "interactive"}
        if v not in allowed:
            raise ValueError(f"message_type must be one of {allowed}")
        return v

    @model_validator(mode='before')
    @classmethod
    def default_next_to_minus_one(cls, data: Any):
        # Centralized fallback: if next is missing/None, set to -1 before validation
        if isinstance(data, dict) and ("next" not in data or data.get("next") is None):
            import logging
            logging.getLogger(__name__).info(
                "send_message.next missing/null; defaulting to -1 (end-of-flow)"
            )
            data = {**data, "next": -1}  # apply fallback
        return data

    @field_validator('next')
    @classmethod
    def validate_next(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("next must be an integer")
        if v < -1:
            raise ValueError("next must be -1 or a non-negative integer")
        return v


class WaitNodeConfig(BaseModel):
    """Configuration for wait nodes."""
    duration: int = Field(..., description="Wait duration", gt=0)
    unit: Literal["seconds", "minutes", "hours", "days"] = Field(default="seconds", description="Unit")
    next: int = Field(..., description="Next node index", ge=0)
    
    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("duration must be a positive number")
        return v


class ConditionNodeConfig(BaseModel):
    """Configuration for condition nodes."""
    variable: str = Field(..., description="Variable to evaluate", min_length=1)
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "contains", "starts_with", "ends_with"] = Field(..., description="Operator")
    value: Any = Field(..., description="Value to compare against")
    true_path: int = Field(..., description="Next node if condition is true", ge=0)
    false_path: int = Field(..., description="Next node if condition is false", ge=0)
    
    @field_validator('variable')
    @classmethod
    def validate_variable(cls, v):
        if not v or not v.strip():
            raise ValueError("variable must be a non-empty string")
        return v.strip()


class WebhookActionNodeConfig(BaseModel):
    """Configuration for webhook_action nodes."""
    url: str = Field(..., description="Webhook URL")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(default="POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Request headers")
    body: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Request body")
    store_response_in: Optional[str] = Field(None, description="State variable to store response")
    next: int = Field(..., description="Next node index", ge=0)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError("url must be a valid HTTP/HTTPS URL")
        return v


class SetAttributeNodeConfig(BaseModel):
    """Configuration for set_attribute nodes."""
    attribute_key: str = Field(..., description="Attribute key name", min_length=1)
    attribute_value: str = Field(..., description="Attribute value (supports {{variables}})")
    value_type: Literal["string", "number", "boolean", "json"] = Field(default="string", description="Value type")
    next: int = Field(..., description="Next node index", ge=0)
    
    @field_validator('attribute_key')
    @classmethod
    def validate_attribute_key(cls, v):
        if not v or not v.strip():
            raise ValueError("attribute_key must be a non-empty string")
        return v.strip()


class FlowNodeSchema(BaseModel):
    """Generic flow node schema."""
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
    next: Optional[int] = Field(None, description="Next node index", ge=0)
    
    @field_validator('config', mode='before')
    @classmethod
    def validate_config_structure(cls, v, info):
        """Ensure config matches the node type."""
        if not isinstance(v, dict):
            raise ValueError("config must be a dictionary")
        if not v:
            raise ValueError("config cannot be empty")
        return v


class FlowExecutionLogResponse(BaseModel):
    """Flow execution log response schema."""
    id: int
    execution_id: int
    node_index: int
    node_type: str
    action: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    executed_at: datetime


class StartFlowRequest(BaseModel):
    """Request to start a flow execution."""
    flow_id: int
    contact_phone: str
    bot_id: int
    initial_state: Optional[Dict[str, Any]] = {}


class ResumeFlowRequest(BaseModel):
    """Request to resume a flow execution."""
    execution_id: int


class CancelFlowRequest(BaseModel):
    """Request to cancel a flow execution."""
    execution_id: int


class UserInputRequest(BaseModel):
    """Request to handle user input."""
    execution_id: int
    message: str
    message_type: str = "text"


class FlowExecutionListResponse(BaseModel):
    """List of flow executions response."""
    executions: List[FlowExecutionResponse]
    total: int
    page: int
    per_page: int


class ContactListResponse(BaseModel):
    """List of contacts response."""
    contacts: List[ContactResponse]
    total: int
    page: int
    per_page: int
