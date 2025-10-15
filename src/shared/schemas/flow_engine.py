"""
Flow Engine schemas for contact management and flow execution.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
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
    message_type: str = Field(..., description="Type: text, template, media, interactive")
    content: Dict[str, Any] = Field(..., description="Message content")
    variables: Optional[List[str]] = Field(default=[], description="Variables to interpolate")
    next: int = Field(..., description="Next node index")


class WaitNodeConfig(BaseModel):
    """Configuration for wait nodes."""
    duration: int = Field(..., description="Wait duration")
    unit: str = Field(default="seconds", description="Unit: seconds, minutes, hours, days")
    next: int = Field(..., description="Next node index")


class ConditionNodeConfig(BaseModel):
    """Configuration for condition nodes."""
    variable: str = Field(..., description="Variable to evaluate")
    operator: str = Field(..., description="Operator: ==, !=, >, <, >=, <=, contains, starts_with, ends_with")
    value: Any = Field(..., description="Value to compare against")
    true_path: int = Field(..., description="Next node if condition is true")
    false_path: int = Field(..., description="Next node if condition is false")


class WebhookActionNodeConfig(BaseModel):
    """Configuration for webhook_action nodes."""
    url: str = Field(..., description="Webhook URL")
    method: str = Field(default="POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(default={}, description="Request headers")
    body: Optional[Dict[str, Any]] = Field(default={}, description="Request body")
    store_response_in: Optional[str] = Field(None, description="State variable to store response")
    next: int = Field(..., description="Next node index")


class SetAttributeNodeConfig(BaseModel):
    """Configuration for set_attribute nodes."""
    attribute_key: str = Field(..., description="Attribute key name")
    attribute_value: str = Field(..., description="Attribute value (supports {{variables}})")
    value_type: Optional[str] = Field(default="string", description="Value type: string, number, boolean, json")
    next: int = Field(..., description="Next node index")


class FlowNodeSchema(BaseModel):
    """Generic flow node schema."""
    type: str = Field(..., description="Node type: send_message, wait, condition, webhook_action, set_attribute")
    config: Union[SendMessageNodeConfig, WaitNodeConfig, ConditionNodeConfig, WebhookActionNodeConfig, SetAttributeNodeConfig]
    next: Optional[int] = Field(None, description="Next node index")


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
