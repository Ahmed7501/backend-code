"""
Trigger schemas for automation trigger system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class TriggerType(str, Enum):
    """Trigger type enum."""
    KEYWORD = "keyword"
    EVENT = "event"
    SCHEDULE = "schedule"


class MatchType(str, Enum):
    """Keyword match type enum."""
    EXACT = "exact"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"


class ScheduleType(str, Enum):
    """Schedule type enum."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class EventType(str, Enum):
    """Event type enum."""
    NEW_CONTACT = "new_contact"
    MESSAGE_RECEIVED = "message_received"
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    FLOW_COMPLETED = "flow_completed"
    FLOW_FAILED = "flow_failed"


class TriggerSchema(BaseModel):
    """Base trigger schema."""
    name: str = Field(..., description="Trigger name")
    bot_id: int = Field(..., description="Bot ID")
    flow_id: int = Field(..., description="Flow ID to execute")
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    is_active: Optional[bool] = Field(default=True, description="Whether trigger is active")
    priority: Optional[int] = Field(default=0, description="Priority (higher = checked first)")


class KeywordTriggerSchema(TriggerSchema):
    """Keyword trigger configuration."""
    trigger_type: TriggerType = TriggerType.KEYWORD
    keywords: List[str] = Field(..., description="List of keywords to match")
    match_type: MatchType = Field(default=MatchType.CONTAINS, description="How to match keywords")
    case_sensitive: Optional[bool] = Field(default=False, description="Case sensitive matching")


class EventTriggerSchema(TriggerSchema):
    """Event trigger configuration."""
    trigger_type: TriggerType = TriggerType.EVENT
    event_type: EventType = Field(..., description="Type of event to trigger on")
    event_conditions: Optional[Dict[str, Any]] = Field(default={}, description="Additional event conditions")


class ScheduleTriggerSchema(TriggerSchema):
    """Schedule trigger configuration."""
    trigger_type: TriggerType = TriggerType.SCHEDULE
    schedule_type: ScheduleType = Field(..., description="Type of schedule")
    schedule_time: str = Field(..., description="Time or cron expression")
    schedule_timezone: Optional[str] = Field(default="UTC", description="Timezone for schedule")


class TriggerResponse(BaseModel):
    """Trigger response schema."""
    id: int
    name: str
    bot_id: int
    flow_id: int
    trigger_type: TriggerType
    is_active: bool
    priority: int
    
    # Keyword fields
    keywords: Optional[List[str]] = None
    match_type: Optional[MatchType] = None
    case_sensitive: Optional[bool] = None
    
    # Event fields
    event_type: Optional[EventType] = None
    event_conditions: Optional[Dict[str, Any]] = None
    
    # Schedule fields
    schedule_type: Optional[ScheduleType] = None
    schedule_time: Optional[str] = None
    schedule_timezone: Optional[str] = None
    last_triggered_at: Optional[datetime] = None
    next_trigger_at: Optional[datetime] = None
    
    # meta_data
    created_at: datetime
    updated_at: Optional[datetime] = None


class TriggerLogResponse(BaseModel):
    """Trigger log response schema."""
    id: int
    trigger_id: int
    contact_id: int
    execution_id: Optional[int] = None
    matched_value: str
    triggered_at: datetime
    success: bool
    error: Optional[str] = None


class CreateTriggerRequest(BaseModel):
    """Request to create a trigger."""
    name: str
    bot_id: int
    flow_id: int
    trigger_type: TriggerType
    is_active: Optional[bool] = True
    priority: Optional[int] = 0
    
    # Keyword trigger fields
    keywords: Optional[List[str]] = None
    match_type: Optional[MatchType] = MatchType.CONTAINS
    case_sensitive: Optional[bool] = False
    
    # Event trigger fields
    event_type: Optional[EventType] = None
    event_conditions: Optional[Dict[str, Any]] = None
    
    # Schedule trigger fields
    schedule_type: Optional[ScheduleType] = None
    schedule_time: Optional[str] = None
    schedule_timezone: Optional[str] = "UTC"


class UpdateTriggerRequest(BaseModel):
    """Request to update a trigger."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    
    # Keyword trigger fields
    keywords: Optional[List[str]] = None
    match_type: Optional[MatchType] = None
    case_sensitive: Optional[bool] = None
    
    # Event trigger fields
    event_type: Optional[EventType] = None
    event_conditions: Optional[Dict[str, Any]] = None
    
    # Schedule trigger fields
    schedule_type: Optional[ScheduleType] = None
    schedule_time: Optional[str] = None
    schedule_timezone: Optional[str] = None


class TestTriggerRequest(BaseModel):
    """Request to test a trigger."""
    test_message: Optional[str] = Field(None, description="Test message for keyword triggers")
    test_event: Optional[Dict[str, Any]] = Field(None, description="Test event data for event triggers")


class TriggerTestResponse(BaseModel):
    """Response from trigger test."""
    matched: bool
    matched_value: Optional[str] = None
    error: Optional[str] = None


class TriggerListResponse(BaseModel):
    """List of triggers response."""
    triggers: List[TriggerResponse]
    total: int
    page: int
    per_page: int


class TriggerLogListResponse(BaseModel):
    """List of trigger logs response."""
    logs: List[TriggerLogResponse]
    total: int
    page: int
    per_page: int


class TriggerStatistics(BaseModel):
    """Trigger statistics."""
    total_triggers: int
    active_triggers: int
    keyword_triggers: int
    event_triggers: int
    schedule_triggers: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_24h_executions: int
