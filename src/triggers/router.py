"""
Trigger API router for automation trigger management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..shared.database import get_sync_session
from ..shared.models.auth import User
from ..shared.models.bot_builder import Trigger
from ..shared.schemas.triggers import (
    TriggerResponse, TriggerListResponse, TriggerLogResponse, TriggerLogListResponse,
    CreateTriggerRequest, UpdateTriggerRequest, TestTriggerRequest, TriggerTestResponse,
    TriggerStatistics
)
from ..auth.auth import get_current_active_user_sync
from ..team.permissions import require_permission, Permission, check_bot_ownership_or_admin
from .crud import (
    create_trigger, get_trigger, get_all_triggers, get_triggers_by_bot,
    update_trigger, delete_trigger, activate_trigger, deactivate_trigger,
    get_trigger_logs, get_trigger_statistics, get_trigger_performance_stats
)
from .matcher import TriggerMatcher
from .scheduler import TriggerScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triggers", tags=["Triggers"])


@router.post("/", response_model=TriggerResponse, status_code=status.HTTP_201_CREATED)
async def create_trigger_endpoint(
    request: CreateTriggerRequest,
    current_user: User = Depends(require_permission(Permission.TRIGGER_CREATE)),
    db: Session = Depends(get_sync_session)
):
    """Create a new trigger."""
    try:
        # Verify user owns the bot
        from ..shared.models.bot_builder import Bot
        bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if not check_bot_ownership_or_admin(bot, current_user, db):
            raise HTTPException(status_code=403, detail="Access denied to this bot")
        
        trigger_data = request.dict()
        trigger = create_trigger(db, trigger_data)
        return TriggerResponse.from_orm(trigger)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trigger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create trigger: {str(e)}")


@router.get("/", response_model=TriggerListResponse)
async def get_all_triggers_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_session)
):
    """Get all triggers with pagination."""
    triggers = get_all_triggers(db, skip, limit)
    total = db.query(Trigger).count()
    
    return TriggerListResponse(
        triggers=[TriggerResponse.from_orm(trigger) for trigger in triggers],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/{trigger_id}", response_model=TriggerResponse)
async def get_trigger_endpoint(
    trigger_id: int,
    db: Session = Depends(get_sync_session)
):
    """Get a trigger by ID."""
    trigger = get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return TriggerResponse.from_orm(trigger)


@router.get("/bot/{bot_id}", response_model=TriggerListResponse)
async def get_triggers_by_bot_endpoint(
    bot_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_session)
):
    """Get triggers for a specific bot."""
    triggers = get_triggers_by_bot(db, bot_id, skip, limit)
    total = len(triggers)  # This is approximate, could be improved with proper counting
    
    return TriggerListResponse(
        triggers=[TriggerResponse.from_orm(trigger) for trigger in triggers],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.put("/{trigger_id}", response_model=TriggerResponse)
async def update_trigger_endpoint(
    trigger_id: int,
    request: UpdateTriggerRequest,
    db: Session = Depends(get_sync_session)
):
    """Update a trigger."""
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    trigger = update_trigger(db, trigger_id, update_data)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    return TriggerResponse.from_orm(trigger)


@router.delete("/{trigger_id}")
async def delete_trigger_endpoint(
    trigger_id: int,
    db: Session = Depends(get_sync_session)
):
    """Delete a trigger."""
    success = delete_trigger(db, trigger_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    return {"message": "Trigger deleted successfully"}


@router.post("/{trigger_id}/activate", response_model=TriggerResponse)
async def activate_trigger_endpoint(
    trigger_id: int,
    db: Session = Depends(get_sync_session)
):
    """Activate a trigger."""
    trigger = activate_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    return TriggerResponse.from_orm(trigger)


@router.post("/{trigger_id}/deactivate", response_model=TriggerResponse)
async def deactivate_trigger_endpoint(
    trigger_id: int,
    db: Session = Depends(get_sync_session)
):
    """Deactivate a trigger."""
    trigger = deactivate_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    return TriggerResponse.from_orm(trigger)


@router.post("/{trigger_id}/test", response_model=TriggerTestResponse)
async def test_trigger_endpoint(
    trigger_id: int,
    request: TestTriggerRequest,
    db: Session = Depends(get_sync_session)
):
    """Test a trigger."""
    trigger = get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    matcher = TriggerMatcher(db)
    
    try:
        if trigger.trigger_type == "keyword" and request.test_message:
            result = await matcher.test_keyword_trigger(trigger, request.test_message)
        elif trigger.trigger_type == "event" and request.test_event:
            result = await matcher.test_event_trigger(trigger, request.test_event)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid test data for trigger type: {trigger.trigger_type}"
            )
        
        return TriggerTestResponse(**result)
    
    except Exception as e:
        logger.error(f"Failed to test trigger {trigger_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test trigger: {str(e)}")


@router.get("/{trigger_id}/logs", response_model=TriggerLogListResponse)
async def get_trigger_logs_endpoint(
    trigger_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_session)
):
    """Get execution logs for a trigger."""
    trigger = get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    logs = get_trigger_logs(db, trigger_id, skip, limit)
    total = len(logs)  # This is approximate
    
    return TriggerLogListResponse(
        logs=[TriggerLogResponse.from_orm(log) for log in logs],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/{trigger_id}/performance", response_model=dict)
async def get_trigger_performance_endpoint(
    trigger_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_sync_session)
):
    """Get performance statistics for a trigger."""
    trigger = get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    stats = get_trigger_performance_stats(db, trigger_id, days)
    return stats


@router.get("/statistics", response_model=TriggerStatistics)
async def get_trigger_statistics_endpoint(db: Session = Depends(get_sync_session)):
    """Get trigger statistics."""
    stats = get_trigger_statistics(db)
    return TriggerStatistics(**stats)


@router.post("/validate-schedule")
async def validate_schedule_endpoint(
    schedule_type: str,
    schedule_time: str,
    timezone: str = "UTC",
    db: Session = Depends(get_sync_session)
):
    """Validate schedule configuration."""
    scheduler = TriggerScheduler(db)
    result = scheduler.validate_schedule_config(schedule_type, schedule_time, timezone)
    
    if result["valid"]:
        return {"valid": True, "message": "Schedule configuration is valid"}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid schedule configuration: {result['error']}"
        )


@router.post("/{trigger_id}/reschedule")
async def reschedule_trigger_endpoint(
    trigger_id: int,
    db: Session = Depends(get_sync_session)
):
    """Reschedule a trigger (for schedule triggers)."""
    trigger = get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    if trigger.trigger_type != "schedule":
        raise HTTPException(
            status_code=400,
            detail="Only schedule triggers can be rescheduled"
        )
    
    scheduler = TriggerScheduler(db)
    success = scheduler.update_trigger_schedule(trigger)
    
    if success:
        return {"message": "Trigger rescheduled successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reschedule trigger")


# Utility endpoints
@router.get("/types/keyword/examples")
async def get_keyword_trigger_examples():
    """Get examples of keyword trigger configurations."""
    return {
        "examples": [
            {
                "name": "Welcome Trigger",
                "description": "Triggers when user says hello",
                "keywords": ["hi", "hello", "hey"],
                "match_type": "exact",
                "case_sensitive": False
            },
            {
                "name": "Help Trigger",
                "description": "Triggers when user asks for help",
                "keywords": ["help", "support", "assistance"],
                "match_type": "contains",
                "case_sensitive": False
            },
            {
                "name": "Phone Number Trigger",
                "description": "Triggers when user sends phone number",
                "keywords": [r"\\+?[1-9]\\d{1,14}"],
                "match_type": "regex",
                "case_sensitive": False
            }
        ]
    }


@router.get("/types/schedule/examples")
async def get_schedule_trigger_examples():
    """Get examples of schedule trigger configurations."""
    return {
        "examples": [
            {
                "name": "Daily Reminder",
                "description": "Send reminder every day at 9 AM",
                "schedule_type": "daily",
                "schedule_time": "09:00",
                "schedule_timezone": "UTC"
            },
            {
                "name": "Weekly Newsletter",
                "description": "Send newsletter every Monday at 10 AM",
                "schedule_type": "weekly",
                "schedule_time": "monday:10:00",
                "schedule_timezone": "UTC"
            },
            {
                "name": "Monthly Report",
                "description": "Send report on 1st of every month at 8 AM",
                "schedule_type": "monthly",
                "schedule_time": "1:08:00",
                "schedule_timezone": "UTC"
            },
            {
                "name": "Complex Schedule",
                "description": "Every weekday at 2 PM using cron",
                "schedule_type": "cron",
                "schedule_time": "0 14 * * 1-5",
                "schedule_timezone": "UTC"
            }
        ]
    }
