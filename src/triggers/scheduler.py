"""
Trigger scheduler service for time-based triggers.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import pytz
from croniter import croniter

from ..shared.models.bot_builder import Trigger
from ..shared.schemas.triggers import ScheduleType

logger = logging.getLogger(__name__)


class TriggerScheduler:
    """Service for scheduling and managing time-based triggers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_next_trigger_time(
        self,
        trigger: Trigger,
        from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate next trigger time for a schedule trigger."""
        if trigger.trigger_type != "schedule":
            return None
        
        if not trigger.schedule_type or not trigger.schedule_time:
            return None
        
        try:
            now = from_time or datetime.utcnow()
            timezone = pytz.timezone(trigger.schedule_timezone or "UTC")
            now_tz = now.replace(tzinfo=pytz.UTC).astimezone(timezone)
            
            if trigger.schedule_type == ScheduleType.ONCE:
                # Parse datetime string for one-time execution
                try:
                    trigger_time = datetime.fromisoformat(trigger.schedule_time.replace('Z', '+00:00'))
                    if trigger_time > now:
                        return trigger_time
                    return None
                except ValueError:
                    logger.error(f"Invalid datetime format for once trigger: {trigger.schedule_time}")
                    return None
            
            elif trigger.schedule_type == ScheduleType.DAILY:
                # Parse time string (HH:MM format)
                try:
                    hour, minute = map(int, trigger.schedule_time.split(':'))
                    next_time = now_tz.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if next_time <= now_tz:
                        next_time += timedelta(days=1)
                    
                    return next_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except ValueError:
                    logger.error(f"Invalid time format for daily trigger: {trigger.schedule_time}")
                    return None
            
            elif trigger.schedule_type == ScheduleType.WEEKLY:
                # Parse day and time (e.g., "monday:09:00")
                try:
                    day_name, time_str = trigger.schedule_time.split(':')
                    hour, minute = map(int, time_str.split(':'))
                    
                    # Map day names to weekday numbers
                    day_map = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6
                    }
                    
                    target_weekday = day_map.get(day_name.lower())
                    if target_weekday is None:
                        logger.error(f"Invalid day name for weekly trigger: {day_name}")
                        return None
                    
                    days_ahead = target_weekday - now_tz.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    
                    next_time = now_tz + timedelta(days=days_ahead)
                    next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    return next_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except (ValueError, KeyError) as e:
                    logger.error(f"Invalid format for weekly trigger: {trigger.schedule_time}, error: {e}")
                    return None
            
            elif trigger.schedule_type == ScheduleType.MONTHLY:
                # Parse day and time (e.g., "15:09:00" for 15th day at 9:00 AM)
                try:
                    day, time_str = trigger.schedule_time.split(':')
                    day = int(day)
                    hour, minute = map(int, time_str.split(':'))
                    
                    # Calculate next occurrence
                    next_time = now_tz.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if next_time <= now_tz:
                        # Move to next month
                        if next_time.month == 12:
                            next_time = next_time.replace(year=next_time.year + 1, month=1)
                        else:
                            next_time = next_time.replace(month=next_time.month + 1)
                    
                    return next_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except ValueError:
                    logger.error(f"Invalid format for monthly trigger: {trigger.schedule_time}")
                    return None
            
            elif trigger.schedule_type == ScheduleType.CRON:
                # Parse cron expression
                try:
                    cron = croniter(trigger.schedule_time, now_tz)
                    next_time = cron.get_next(datetime)
                    return next_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except Exception as e:
                    logger.error(f"Invalid cron expression: {trigger.schedule_time}, error: {e}")
                    return None
            
            else:
                logger.error(f"Unknown schedule type: {trigger.schedule_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error calculating next trigger time: {str(e)}")
            return None
    
    def schedule_trigger(
        self,
        trigger: Trigger,
        contact_id: int
    ) -> Optional[str]:
        """Schedule a trigger execution via Celery."""
        try:
            from .tasks import execute_scheduled_trigger
            
            next_time = self.calculate_next_trigger_time(trigger)
            if not next_time:
                logger.warning(f"Could not calculate next trigger time for trigger {trigger.id}")
                return None
            
            # Calculate delay in seconds
            delay = (next_time - datetime.utcnow()).total_seconds()
            if delay <= 0:
                logger.warning(f"Trigger {trigger.id} is already due, executing immediately")
                delay = 1  # Execute in 1 second
            
            # Schedule Celery task
            task = execute_scheduled_trigger.apply_async(
                args=[trigger.id, contact_id],
                countdown=delay
            )
            
            # Update trigger with next execution time
            trigger.next_trigger_at = next_time
            self.db.commit()
            
            logger.info(f"Scheduled trigger {trigger.id} for {next_time} (task: {task.id})")
            return task.id
        
        except Exception as e:
            logger.error(f"Error scheduling trigger {trigger.id}: {str(e)}")
            return None
    
    def update_trigger_schedule(
        self,
        trigger: Trigger
    ) -> bool:
        """Update trigger's next execution time."""
        try:
            if trigger.trigger_type != "schedule":
                return True
            
            next_time = self.calculate_next_trigger_time(trigger)
            if next_time:
                trigger.next_trigger_at = next_time
                self.db.commit()
                logger.info(f"Updated schedule for trigger {trigger.id}: next execution at {next_time}")
                return True
            else:
                logger.warning(f"Could not calculate next time for trigger {trigger.id}")
                return False
        
        except Exception as e:
            logger.error(f"Error updating trigger schedule: {str(e)}")
            return False
    
    def get_due_triggers(self) -> list:
        """Get triggers that are due for execution."""
        try:
            now = datetime.utcnow()
            
            due_triggers = (
                self.db.query(Trigger)
                .filter(
                    Trigger.trigger_type == "schedule",
                    Trigger.is_active == True,
                    Trigger.next_trigger_at <= now
                )
                .all()
            )
            
            return due_triggers
        
        except Exception as e:
            logger.error(f"Error getting due triggers: {str(e)}")
            return []
    
    def validate_schedule_config(
        self,
        schedule_type: str,
        schedule_time: str,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Validate schedule configuration."""
        try:
            if schedule_type == ScheduleType.ONCE:
                # Validate datetime format
                datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
                return {"valid": True, "error": None}
            
            elif schedule_type == ScheduleType.DAILY:
                # Validate time format (HH:MM)
                hour, minute = map(int, schedule_time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return {"valid": False, "error": "Invalid hour or minute"}
                return {"valid": True, "error": None}
            
            elif schedule_type == ScheduleType.WEEKLY:
                # Validate day:time format
                day_name, time_str = schedule_time.split(':')
                day_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                if day_name.lower() not in day_map:
                    return {"valid": False, "error": f"Invalid day name: {day_name}"}
                
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return {"valid": False, "error": "Invalid hour or minute"}
                return {"valid": True, "error": None}
            
            elif schedule_type == ScheduleType.MONTHLY:
                # Validate day:time format
                day, time_str = schedule_time.split(':')
                day = int(day)
                if not (1 <= day <= 31):
                    return {"valid": False, "error": "Invalid day (must be 1-31)"}
                
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return {"valid": False, "error": "Invalid hour or minute"}
                return {"valid": True, "error": None}
            
            elif schedule_type == ScheduleType.CRON:
                # Validate cron expression
                croniter(schedule_time, datetime.utcnow())
                return {"valid": True, "error": None}
            
            else:
                return {"valid": False, "error": f"Unknown schedule type: {schedule_type}"}
        
        except Exception as e:
            return {"valid": False, "error": str(e)}
