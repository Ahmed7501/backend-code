"""
CRUD operations for analytics and reporting.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from ..shared.models.bot_builder import (
    DailyMessageStats, 
    HourlyMessageStats, 
    WhatsAppMessage, 
    Contact, 
    FlowExecution, 
    TriggerLog,
    Bot
)

logger = logging.getLogger(__name__)


def aggregate_daily_stats(db: Session, target_date: date, bot_id: Optional[int] = None) -> List[DailyMessageStats]:
    """Aggregate statistics for a specific date."""
    try:
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Get bots to aggregate for
        if bot_id:
            bots = db.query(Bot).filter(Bot.id == bot_id).all()
        else:
            bots = db.query(Bot).all()
        
        aggregated_stats = []
        
        for bot in bots:
            # Check if stats already exist for this date
            existing_stats = db.query(DailyMessageStats).filter(
                and_(
                    DailyMessageStats.bot_id == bot.id,
                    DailyMessageStats.date == start_datetime
                )
            ).first()
            
            if existing_stats:
                logger.info(f"Daily stats already exist for bot {bot.id} on {target_date}")
                aggregated_stats.append(existing_stats)
                continue
            
            # Aggregate message statistics
            message_stats = db.query(
                func.count(WhatsAppMessage.id).label('total_messages'),
                func.sum(func.case([(WhatsAppMessage.direction == 'inbound', 1)], else_=0)).label('inbound_messages'),
                func.sum(func.case([(WhatsAppMessage.direction == 'outbound', 1)], else_=0)).label('outbound_messages'),
                func.sum(func.case([(WhatsAppMessage.message_type == 'text', 1)], else_=0)).label('text_messages'),
                func.sum(func.case([(WhatsAppMessage.message_type == 'template', 1)], else_=0)).label('template_messages'),
                func.sum(func.case([(WhatsAppMessage.message_type == 'media', 1)], else_=0)).label('media_messages'),
                func.sum(func.case([(WhatsAppMessage.message_type == 'interactive', 1)], else_=0)).label('interactive_messages'),
                func.sum(func.case([(WhatsAppMessage.status == 'sent', 1)], else_=0)).label('sent_count'),
                func.sum(func.case([(WhatsAppMessage.status == 'delivered', 1)], else_=0)).label('delivered_count'),
                func.sum(func.case([(WhatsAppMessage.status == 'read', 1)], else_=0)).label('read_count'),
                func.sum(func.case([(WhatsAppMessage.status == 'failed', 1)], else_=0)).label('failed_count')
            ).filter(
                and_(
                    WhatsAppMessage.bot_id == bot.id,
                    WhatsAppMessage.created_at >= start_datetime,
                    WhatsAppMessage.created_at <= end_datetime
                )
            ).first()
            
            # Count active contacts (unique contacts who sent/received messages)
            active_contacts = db.query(func.count(func.distinct(WhatsAppMessage.recipient_phone))).filter(
                and_(
                    WhatsAppMessage.bot_id == bot.id,
                    WhatsAppMessage.created_at >= start_datetime,
                    WhatsAppMessage.created_at <= end_datetime
                )
            ).scalar() or 0
            
            # Count new contacts created on this day
            new_contacts = db.query(func.count(Contact.id)).filter(
                and_(
                    Contact.created_at >= start_datetime,
                    Contact.created_at <= end_datetime
                )
            ).scalar() or 0
            
            # Aggregate flow statistics
            flow_stats = db.query(
                func.sum(func.case([(FlowExecution.status == 'running', 1)], else_=0)).label('flows_started'),
                func.sum(func.case([(FlowExecution.status == 'completed', 1)], else_=0)).label('flows_completed'),
                func.sum(func.case([(FlowExecution.status == 'failed', 1)], else_=0)).label('flows_failed')
            ).filter(
                and_(
                    FlowExecution.bot_id == bot.id,
                    FlowExecution.started_at >= start_datetime,
                    FlowExecution.started_at <= end_datetime
                )
            ).first()
            
            # Count triggers fired
            triggers_fired = db.query(func.count(TriggerLog.id)).filter(
                and_(
                    TriggerLog.triggered_at >= start_datetime,
                    TriggerLog.triggered_at <= end_datetime
                )
            ).scalar() or 0
            
            # Create daily stats record
            daily_stats = DailyMessageStats(
                bot_id=bot.id,
                date=start_datetime,
                total_messages=message_stats.total_messages or 0,
                inbound_messages=message_stats.inbound_messages or 0,
                outbound_messages=message_stats.outbound_messages or 0,
                text_messages=message_stats.text_messages or 0,
                template_messages=message_stats.template_messages or 0,
                media_messages=message_stats.media_messages or 0,
                interactive_messages=message_stats.interactive_messages or 0,
                sent_count=message_stats.sent_count or 0,
                delivered_count=message_stats.delivered_count or 0,
                read_count=message_stats.read_count or 0,
                failed_count=message_stats.failed_count or 0,
                active_contacts=active_contacts,
                new_contacts=new_contacts,
                flows_started=flow_stats.flows_started or 0,
                flows_completed=flow_stats.flows_completed or 0,
                flows_failed=flow_stats.flows_failed or 0,
                triggers_fired=triggers_fired
            )
            
            db.add(daily_stats)
            aggregated_stats.append(daily_stats)
            
            logger.info(f"Aggregated daily stats for bot {bot.id} on {target_date}: {daily_stats.total_messages} messages")
        
        db.commit()
        return aggregated_stats
        
    except Exception as e:
        logger.error(f"Failed to aggregate daily stats for {target_date}: {e}")
        db.rollback()
        raise


def get_daily_stats(db: Session, start_date: datetime, end_date: datetime, bot_id: Optional[int] = None) -> List[DailyMessageStats]:
    """Get daily statistics for a date range."""
    query = db.query(DailyMessageStats).filter(
        and_(
            DailyMessageStats.date >= start_date,
            DailyMessageStats.date <= end_date
        )
    )
    
    if bot_id:
        query = query.filter(DailyMessageStats.bot_id == bot_id)
    
    return query.order_by(DailyMessageStats.date).all()


def get_overview_stats(db: Session, period: str, bot_id: Optional[int] = None) -> Dict[str, Any]:
    """Get overview statistics for a period."""
    end_date = datetime.utcnow()
    
    if period == "today":
        start_date = datetime.combine(end_date.date(), datetime.min.time())
    elif period == "7days":
        start_date = end_date - timedelta(days=7)
    elif period == "30days":
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError(f"Unsupported period: {period}")
    
    # Get daily stats for the period
    daily_stats = get_daily_stats(db, start_date, end_date, bot_id)
    
    if not daily_stats:
        return {
            "total_messages": 0,
            "active_contacts": 0,
            "delivery_rate": 0.0,
            "flow_completion_rate": 0.0,
            "top_message_types": {},
            "trends": {}
        }
    
    # Calculate aggregated metrics
    total_messages = sum(stat.total_messages for stat in daily_stats)
    total_sent = sum(stat.sent_count for stat in daily_stats)
    total_delivered = sum(stat.delivered_count for stat in daily_stats)
    total_flows_started = sum(stat.flows_started for stat in daily_stats)
    total_flows_completed = sum(stat.flows_completed for stat in daily_stats)
    
    # Calculate delivery rate
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
    
    # Calculate flow completion rate
    flow_completion_rate = (total_flows_completed / total_flows_started * 100) if total_flows_started > 0 else 0.0
    
    # Get message type distribution
    message_types = {
        "text": sum(stat.text_messages for stat in daily_stats),
        "template": sum(stat.template_messages for stat in daily_stats),
        "media": sum(stat.media_messages for stat in daily_stats),
        "interactive": sum(stat.interactive_messages for stat in daily_stats)
    }
    
    # Get active contacts (max active contacts on any single day)
    active_contacts = max(stat.active_contacts for stat in daily_stats) if daily_stats else 0
    
    # Calculate trends (compare with previous period)
    trends = calculate_trends(db, start_date, end_date, bot_id)
    
    return {
        "total_messages": total_messages,
        "active_contacts": active_contacts,
        "delivery_rate": round(delivery_rate, 2),
        "flow_completion_rate": round(flow_completion_rate, 2),
        "top_message_types": message_types,
        "trends": trends
    }


def calculate_delivery_rate(db: Session, bot_id: Optional[int], start_date: datetime, end_date: datetime) -> float:
    """Calculate delivery rate for a period."""
    query = db.query(
        func.sum(func.case([(WhatsAppMessage.status == 'sent', 1)], else_=0)).label('sent'),
        func.sum(func.case([(WhatsAppMessage.status == 'delivered', 1)], else_=0)).label('delivered')
    ).filter(
        and_(
            WhatsAppMessage.created_at >= start_date,
            WhatsAppMessage.created_at <= end_date
        )
    )
    
    if bot_id:
        query = query.filter(WhatsAppMessage.bot_id == bot_id)
    
    result = query.first()
    
    if result.sent and result.sent > 0:
        return round((result.delivered / result.sent) * 100, 2)
    return 0.0


def get_active_contacts_count(db: Session, bot_id: Optional[int], target_date: date) -> int:
    """Count active contacts for a specific date."""
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    query = db.query(func.count(func.distinct(WhatsAppMessage.recipient_phone))).filter(
        and_(
            WhatsAppMessage.created_at >= start_datetime,
            WhatsAppMessage.created_at <= end_datetime
        )
    )
    
    if bot_id:
        query = query.filter(WhatsAppMessage.bot_id == bot_id)
    
    return query.scalar() or 0


def get_message_type_distribution(db: Session, bot_id: Optional[int], start_date: datetime, end_date: datetime) -> Dict[str, int]:
    """Get message type distribution for a period."""
    query = db.query(
        WhatsAppMessage.message_type,
        func.count(WhatsAppMessage.id).label('count')
    ).filter(
        and_(
            WhatsAppMessage.created_at >= start_date,
            WhatsAppMessage.created_at <= end_date
        )
    )
    
    if bot_id:
        query = query.filter(WhatsAppMessage.bot_id == bot_id)
    
    results = query.group_by(WhatsAppMessage.message_type).all()
    
    return {result.message_type: result.count for result in results}


def get_flow_completion_rate(db: Session, bot_id: Optional[int], start_date: datetime, end_date: datetime) -> float:
    """Calculate flow completion rate for a period."""
    query = db.query(
        func.sum(func.case([(FlowExecution.status == 'completed', 1)], else_=0)).label('completed'),
        func.sum(func.case([(FlowExecution.status.in_(['completed', 'failed']), 1)], else_=0)).label('total')
    ).filter(
        and_(
            FlowExecution.started_at >= start_date,
            FlowExecution.started_at <= end_date
        )
    )
    
    if bot_id:
        query = query.filter(FlowExecution.bot_id == bot_id)
    
    result = query.first()
    
    if result.total and result.total > 0:
        return round((result.completed / result.total) * 100, 2)
    return 0.0


def calculate_trends(db: Session, current_start: datetime, current_end: datetime, bot_id: Optional[int]) -> Dict[str, float]:
    """Calculate trends by comparing current period with previous period."""
    period_duration = current_end - current_start
    previous_end = current_start
    previous_start = previous_end - period_duration
    
    # Get current period stats
    current_stats = get_overview_stats(db, "custom", bot_id)  # We'll need to modify this
    
    # Get previous period stats
    previous_stats = get_overview_stats(db, "custom", bot_id)  # We'll need to modify this
    
    trends = {}
    
    if previous_stats["total_messages"] > 0:
        trends["messages_growth"] = round(
            ((current_stats["total_messages"] - previous_stats["total_messages"]) / previous_stats["total_messages"]) * 100, 2
        )
    else:
        trends["messages_growth"] = 100.0 if current_stats["total_messages"] > 0 else 0.0
    
    if previous_stats["active_contacts"] > 0:
        trends["contacts_growth"] = round(
            ((current_stats["active_contacts"] - previous_stats["active_contacts"]) / previous_stats["active_contacts"]) * 100, 2
        )
    else:
        trends["contacts_growth"] = 100.0 if current_stats["active_contacts"] > 0 else 0.0
    
    trends["delivery_rate_change"] = round(
        current_stats["delivery_rate"] - previous_stats["delivery_rate"], 2
    )
    
    return trends


def aggregate_hourly_stats(db: Session, target_hour: datetime, bot_id: Optional[int] = None) -> List[HourlyMessageStats]:
    """Aggregate hourly statistics."""
    try:
        start_hour = target_hour.replace(minute=0, second=0, microsecond=0)
        end_hour = start_hour + timedelta(hours=1)
        
        # Get bots to aggregate for
        if bot_id:
            bots = db.query(Bot).filter(Bot.id == bot_id).all()
        else:
            bots = db.query(Bot).all()
        
        aggregated_stats = []
        
        for bot in bots:
            # Check if stats already exist for this hour
            existing_stats = db.query(HourlyMessageStats).filter(
                and_(
                    HourlyMessageStats.bot_id == bot.id,
                    HourlyMessageStats.hour == start_hour
                )
            ).first()
            
            if existing_stats:
                aggregated_stats.append(existing_stats)
                continue
            
            # Aggregate message statistics for the hour
            message_stats = db.query(
                func.count(WhatsAppMessage.id).label('total_messages'),
                func.sum(func.case([(WhatsAppMessage.direction == 'inbound', 1)], else_=0)).label('inbound_messages'),
                func.sum(func.case([(WhatsAppMessage.direction == 'outbound', 1)], else_=0)).label('outbound_messages')
            ).filter(
                and_(
                    WhatsAppMessage.bot_id == bot.id,
                    WhatsAppMessage.created_at >= start_hour,
                    WhatsAppMessage.created_at < end_hour
                )
            ).first()
            
            # Create hourly stats record
            hourly_stats = HourlyMessageStats(
                bot_id=bot.id,
                hour=start_hour,
                total_messages=message_stats.total_messages or 0,
                inbound_messages=message_stats.inbound_messages or 0,
                outbound_messages=message_stats.outbound_messages or 0
            )
            
            db.add(hourly_stats)
            aggregated_stats.append(hourly_stats)
        
        db.commit()
        return aggregated_stats
        
    except Exception as e:
        logger.error(f"Failed to aggregate hourly stats for {target_hour}: {e}")
        db.rollback()
        raise


def cleanup_old_stats(db: Session, days_to_keep_hourly: int = 7, days_to_keep_daily: int = 90):
    """Clean up old statistics."""
    try:
        # Clean up hourly stats older than specified days
        hourly_cutoff = datetime.utcnow() - timedelta(days=days_to_keep_hourly)
        hourly_deleted = db.query(HourlyMessageStats).filter(
            HourlyMessageStats.hour < hourly_cutoff
        ).delete()
        
        # Clean up daily stats older than specified days
        daily_cutoff = datetime.utcnow() - timedelta(days=days_to_keep_daily)
        daily_deleted = db.query(DailyMessageStats).filter(
            DailyMessageStats.date < daily_cutoff
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {hourly_deleted} hourly stats and {daily_deleted} daily stats")
        return {"hourly_deleted": hourly_deleted, "daily_deleted": daily_deleted}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old stats: {e}")
        db.rollback()
        raise
