"""
Pydantic schemas for analytics and reporting.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DailyStatsResponse(BaseModel):
    """Response schema for daily statistics."""
    date: datetime
    bot_id: int
    total_messages: int
    inbound_messages: int
    outbound_messages: int
    delivery_rate: float  # Calculated field
    active_contacts: int
    new_contacts: int
    flows_started: int
    flows_completed: int
    flows_failed: int
    triggers_fired: int

    class Config:
       from_attributes = True


class AnalyticsOverviewResponse(BaseModel):
    """Response schema for analytics overview."""
    period: str  # "today", "7days", "30days"
    bot_id: Optional[int]
    total_messages: int
    active_contacts: int
    delivery_rate: float
    average_response_time: Optional[float]
    top_message_types: Dict[str, int]
    flow_completion_rate: float
    trends: Dict[str, Any]  # Growth percentages

    class Config:
       from_attributes = True


class AnalyticsTrendsResponse(BaseModel):
    """Response schema for analytics trends."""
    start_date: datetime
    end_date: datetime
    bot_id: Optional[int]
    daily_stats: List[DailyStatsResponse]
    total_messages_trend: List[Dict[str, Any]]
    active_contacts_trend: List[Dict[str, Any]]
    delivery_rate_trend: List[Dict[str, Any]]

    class Config:
       from_attributes = True


class BotPerformanceResponse(BaseModel):
    """Response schema for bot performance metrics."""
    bot_id: int
    bot_name: str
    total_messages: int
    active_contacts: int
    delivery_rate: float
    flow_completion_rate: float
    average_flows_per_contact: float

    class Config:
       from_attributes = True


class DeliveryRatesResponse(BaseModel):
    """Response schema for delivery rate statistics."""
    start_date: datetime
    end_date: datetime
    bot_id: Optional[int]
    granularity: str  # "hourly" or "daily"
    delivery_rates: List[Dict[str, Any]]
    average_delivery_rate: float
    total_sent: int
    total_delivered: int
    total_read: int
    total_failed: int

    class Config:
       from_attributes = True


class ActiveContactsResponse(BaseModel):
    """Response schema for active contacts statistics."""
    period: str
    bot_id: Optional[int]
    active_contacts: int
    new_contacts: int
    returning_contacts: int
    contacts_growth_rate: float
    daily_active_contacts: List[Dict[str, Any]]

    class Config:
       from_attributes = True


class MessageDistributionResponse(BaseModel):
    """Response schema for message type distribution."""
    period: str
    bot_id: Optional[int]
    total_messages: int
    message_types: Dict[str, int]
    inbound_distribution: Dict[str, int]
    outbound_distribution: Dict[str, int]
    percentage_breakdown: Dict[str, float]

    class Config:
       from_attributes = True


class ManualAggregationRequest(BaseModel):
    """Request schema for manual aggregation trigger."""
    date: Optional[datetime] = None
    bot_id: Optional[int] = None
    force_recalculate: bool = False


class ManualAggregationResponse(BaseModel):
    """Response schema for manual aggregation."""
    success: bool
    message: str
    aggregated_bots: List[int]
    aggregated_date: datetime
    processing_time: float
