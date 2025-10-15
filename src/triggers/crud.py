"""
CRUD operations for trigger management.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from ..shared.models.bot_builder import Trigger, TriggerLog
from ..shared.schemas.triggers import TriggerType


# Trigger CRUD operations
def create_trigger(db: Session, trigger_data: Dict[str, Any]) -> Trigger:
    """Create a new trigger."""
    trigger = Trigger(
        name=trigger_data["name"],
        bot_id=trigger_data["bot_id"],
        flow_id=trigger_data["flow_id"],
        trigger_type=trigger_data["trigger_type"],
        is_active=trigger_data.get("is_active", True),
        priority=trigger_data.get("priority", 0),
        
        # Keyword fields
        keywords=trigger_data.get("keywords"),
        match_type=trigger_data.get("match_type"),
        case_sensitive=trigger_data.get("case_sensitive"),
        
        # Event fields
        event_type=trigger_data.get("event_type"),
        event_conditions=trigger_data.get("event_conditions"),
        
        # Schedule fields
        schedule_type=trigger_data.get("schedule_type"),
        schedule_time=trigger_data.get("schedule_time"),
        schedule_timezone=trigger_data.get("schedule_timezone", "UTC")
    )
    
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    
    # Calculate next trigger time for schedule triggers
    if trigger.trigger_type == TriggerType.SCHEDULE:
        from .scheduler import TriggerScheduler
        scheduler = TriggerScheduler(db)
        scheduler.update_trigger_schedule(trigger)
    
    return trigger


def get_trigger(db: Session, trigger_id: int) -> Optional[Trigger]:
    """Get a trigger by ID."""
    return db.query(Trigger).filter(Trigger.id == trigger_id).first()


def get_all_triggers(db: Session, skip: int = 0, limit: int = 100) -> List[Trigger]:
    """Get all triggers with pagination."""
    return (
        db.query(Trigger)
        .order_by(desc(Trigger.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_triggers_by_bot(db: Session, bot_id: int, skip: int = 0, limit: int = 100) -> List[Trigger]:
    """Get all triggers for a specific bot."""
    return (
        db.query(Trigger)
        .filter(Trigger.bot_id == bot_id)
        .order_by(desc(Trigger.priority), desc(Trigger.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_keyword_triggers(db: Session, bot_id: int) -> List[Trigger]:
    """Get active keyword triggers for a bot."""
    return (
        db.query(Trigger)
        .filter(
            Trigger.bot_id == bot_id,
            Trigger.trigger_type == TriggerType.KEYWORD,
            Trigger.is_active == True
        )
        .order_by(desc(Trigger.priority))
        .all()
    )


def get_active_event_triggers(db: Session, bot_id: int, event_type: str) -> List[Trigger]:
    """Get active event triggers for a bot and event type."""
    return (
        db.query(Trigger)
        .filter(
            Trigger.bot_id == bot_id,
            Trigger.trigger_type == TriggerType.EVENT,
            Trigger.event_type == event_type,
            Trigger.is_active == True
        )
        .order_by(desc(Trigger.priority))
        .all()
    )


def get_due_scheduled_triggers(db: Session) -> List[Trigger]:
    """Get triggers that are due for execution."""
    now = datetime.utcnow()
    return (
        db.query(Trigger)
        .filter(
            Trigger.trigger_type == TriggerType.SCHEDULE,
            Trigger.is_active == True,
            Trigger.next_trigger_at <= now
        )
        .all()
    )


def get_scheduled_triggers_by_bot(db: Session, bot_id: int) -> List[Trigger]:
    """Get all scheduled triggers for a bot."""
    return (
        db.query(Trigger)
        .filter(
            Trigger.bot_id == bot_id,
            Trigger.trigger_type == TriggerType.SCHEDULE,
            Trigger.is_active == True
        )
        .order_by(Trigger.next_trigger_at)
        .all()
    )


def update_trigger(db: Session, trigger_id: int, update_data: Dict[str, Any]) -> Optional[Trigger]:
    """Update a trigger."""
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        return None
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(trigger, field) and value is not None:
            setattr(trigger, field, value)
    
    trigger.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(trigger)
    
    # Update schedule if it's a schedule trigger
    if trigger.trigger_type == TriggerType.SCHEDULE:
        from .scheduler import TriggerScheduler
        scheduler = TriggerScheduler(db)
        scheduler.update_trigger_schedule(trigger)
    
    return trigger


def delete_trigger(db: Session, trigger_id: int) -> bool:
    """Delete a trigger."""
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        return False
    
    db.delete(trigger)
    db.commit()
    return True


def activate_trigger(db: Session, trigger_id: int) -> Optional[Trigger]:
    """Activate a trigger."""
    return update_trigger(db, trigger_id, {"is_active": True})


def deactivate_trigger(db: Session, trigger_id: int) -> Optional[Trigger]:
    """Deactivate a trigger."""
    return update_trigger(db, trigger_id, {"is_active": False})


# Trigger Log CRUD operations
def create_trigger_log(db: Session, log_data: Dict[str, Any]) -> TriggerLog:
    """Create a new trigger log entry."""
    log = TriggerLog(
        trigger_id=log_data["trigger_id"],
        contact_id=log_data["contact_id"],
        execution_id=log_data.get("execution_id"),
        matched_value=log_data["matched_value"],
        success=log_data.get("success", True),
        error=log_data.get("error")
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_trigger_logs(db: Session, trigger_id: int, skip: int = 0, limit: int = 100) -> List[TriggerLog]:
    """Get logs for a specific trigger."""
    return (
        db.query(TriggerLog)
        .filter(TriggerLog.trigger_id == trigger_id)
        .order_by(desc(TriggerLog.triggered_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_trigger_log(db: Session, log_id: int) -> Optional[TriggerLog]:
    """Get a trigger log by ID."""
    return db.query(TriggerLog).filter(TriggerLog.id == log_id).first()


def get_recent_trigger_logs(db: Session, hours: int = 24, limit: int = 100) -> List[TriggerLog]:
    """Get recent trigger logs."""
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(TriggerLog)
        .filter(TriggerLog.triggered_at >= since)
        .order_by(desc(TriggerLog.triggered_at))
        .limit(limit)
        .all()
    )


def delete_trigger_logs(db: Session, trigger_id: int) -> int:
    """Delete all logs for a trigger."""
    logs = db.query(TriggerLog).filter(TriggerLog.trigger_id == trigger_id).all()
    count = len(logs)
    for log in logs:
        db.delete(log)
    db.commit()
    return count


# Utility functions
def get_trigger_count_by_type(db: Session, trigger_type: str) -> int:
    """Get count of triggers by type."""
    return db.query(Trigger).filter(Trigger.trigger_type == trigger_type).count()


def get_trigger_count_by_bot(db: Session, bot_id: int) -> int:
    """Get count of triggers for a bot."""
    return db.query(Trigger).filter(Trigger.bot_id == bot_id).count()


def get_active_trigger_count(db: Session) -> int:
    """Get count of active triggers."""
    return db.query(Trigger).filter(Trigger.is_active == True).count()


def get_trigger_statistics(db: Session) -> Dict[str, int]:
    """Get trigger statistics."""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    total_triggers = db.query(Trigger).count()
    active_triggers = get_active_trigger_count(db)
    
    keyword_triggers = get_trigger_count_by_type(db, TriggerType.KEYWORD)
    event_triggers = get_trigger_count_by_type(db, TriggerType.EVENT)
    schedule_triggers = get_trigger_count_by_type(db, TriggerType.SCHEDULE)
    
    total_executions = db.query(TriggerLog).count()
    successful_executions = db.query(TriggerLog).filter(TriggerLog.success == True).count()
    failed_executions = db.query(TriggerLog).filter(TriggerLog.success == False).count()
    last_24h_executions = db.query(TriggerLog).filter(TriggerLog.triggered_at >= last_24h).count()
    
    return {
        "total_triggers": total_triggers,
        "active_triggers": active_triggers,
        "keyword_triggers": keyword_triggers,
        "event_triggers": event_triggers,
        "schedule_triggers": schedule_triggers,
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "last_24h_executions": last_24h_executions
    }


def get_trigger_performance_stats(db: Session, trigger_id: int, days: int = 30) -> Dict[str, Any]:
    """Get performance statistics for a specific trigger."""
    since = datetime.utcnow() - timedelta(days=days)
    
    logs = (
        db.query(TriggerLog)
        .filter(
            TriggerLog.trigger_id == trigger_id,
            TriggerLog.triggered_at >= since
        )
        .all()
    )
    
    total_executions = len(logs)
    successful_executions = len([log for log in logs if log.success])
    failed_executions = total_executions - successful_executions
    
    # Calculate success rate
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
    
    # Get most common matched values
    matched_values = {}
    for log in logs:
        value = log.matched_value
        matched_values[value] = matched_values.get(value, 0) + 1
    
    most_common_matches = sorted(matched_values.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "success_rate": round(success_rate, 2),
        "most_common_matches": most_common_matches,
        "period_days": days
    }
