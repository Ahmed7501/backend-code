"""
Celery tasks for trigger automation system.
"""

import logging
from datetime import datetime, timedelta
from celery import current_task
from sqlalchemy.orm import Session

from ..flow_engine.celery_app import celery_app
from ..flow_engine.engine import FlowEngine
from ..shared.database import get_sync_session
from .crud import get_trigger, get_due_scheduled_triggers, create_trigger_log
from .scheduler import TriggerScheduler

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="src.triggers.tasks.execute_scheduled_trigger")
def execute_scheduled_trigger(self, trigger_id: int, contact_id: int):
    """Execute a scheduled trigger."""
    try:
        logger.info(f"Executing scheduled trigger {trigger_id} for contact {contact_id}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Get trigger
        trigger = get_trigger(db, trigger_id)
        if not trigger:
            logger.error(f"Trigger {trigger_id} not found")
            return {"success": False, "error": "Trigger not found"}
        
        if not trigger.is_active:
            logger.warning(f"Trigger {trigger_id} is not active")
            return {"success": False, "error": "Trigger is not active"}
        
        # Get contact
        from ..flow_engine.crud import get_contact
        contact = get_contact(db, contact_id)
        if not contact:
            logger.error(f"Contact {contact_id} not found")
            return {"success": False, "error": "Contact not found"}
        
        # Execute flow
        engine = FlowEngine(db)
        execution = engine.start_flow(
            flow_id=trigger.flow_id,
            contact_phone=contact.phone_number,
            bot_id=trigger.bot_id,
            initial_state={"triggered_by": trigger.name, "trigger_type": "schedule"}
        )
        
        # Log trigger execution
        create_trigger_log(db, {
            "trigger_id": trigger_id,
            "contact_id": contact_id,
            "execution_id": execution.id,
            "matched_value": f"scheduled_{trigger.schedule_type}",
            "success": True
        })
        
        # Update trigger last execution time
        trigger.last_triggered_at = datetime.utcnow()
        
        # Calculate next execution time for recurring triggers
        if trigger.schedule_type != "once":
            scheduler = TriggerScheduler(db)
            scheduler.update_trigger_schedule(trigger)
        
        db.commit()
        
        logger.info(f"Successfully executed scheduled trigger {trigger_id}")
        return {"success": True, "execution_id": execution.id}
    
    except Exception as e:
        logger.error(f"Failed to execute scheduled trigger {trigger_id}: {str(e)}")
        
        # Log failed execution
        try:
            db = next(get_sync_session())
            create_trigger_log(db, {
                "trigger_id": trigger_id,
                "contact_id": contact_id,
                "matched_value": f"scheduled_{trigger.schedule_type if trigger else 'unknown'}",
                "success": False,
                "error": str(e)
            })
        except Exception as log_error:
            logger.error(f"Failed to log trigger execution error: {log_error}")
        
        # Retry the task if it's a temporary error
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying execute_scheduled_trigger task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.triggers.tasks.check_pending_triggers")
def check_pending_triggers():
    """Check for triggers that are due for execution."""
    try:
        logger.info("Checking for pending triggers")
        
        # Get database session
        db = next(get_sync_session())
        
        # Get due triggers
        due_triggers = get_due_scheduled_triggers(db)
        
        executed_count = 0
        for trigger in due_triggers:
            try:
                # Get all contacts for this bot (or specific contacts if configured)
                from ..flow_engine.crud import get_all_contacts
                contacts = get_all_contacts(db, limit=1000)  # Get all contacts
                
                for contact in contacts:
                    # Execute trigger for each contact
                    task = execute_scheduled_trigger.delay(trigger.id, contact.id)
                    executed_count += 1
                    logger.info(f"Scheduled trigger {trigger.id} for contact {contact.id} (task: {task.id})")
                
            except Exception as e:
                logger.error(f"Failed to process trigger {trigger.id}: {str(e)}")
        
        logger.info(f"Processed {executed_count} pending trigger executions")
        return {"success": True, "executed_count": executed_count}
    
    except Exception as e:
        logger.error(f"Failed to check pending triggers: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.triggers.tasks.update_trigger_schedules")
def update_trigger_schedules():
    """Update next trigger times for all schedule triggers."""
    try:
        logger.info("Updating trigger schedules")
        
        # Get database session
        db = next(get_sync_session())
        
        # Get all active schedule triggers
        from ..shared.models.bot_builder import Trigger
        schedule_triggers = (
            db.query(Trigger)
            .filter(
                Trigger.trigger_type == "schedule",
                Trigger.is_active == True
            )
            .all()
        )
        
        updated_count = 0
        scheduler = TriggerScheduler(db)
        
        for trigger in schedule_triggers:
            try:
                if scheduler.update_trigger_schedule(trigger):
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update schedule for trigger {trigger.id}: {str(e)}")
        
        logger.info(f"Updated {updated_count} trigger schedules")
        return {"success": True, "updated_count": updated_count}
    
    except Exception as e:
        logger.error(f"Failed to update trigger schedules: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="src.triggers.tasks.execute_keyword_trigger")
def execute_keyword_trigger(self, trigger_id: int, contact_id: int, matched_message: str):
    """Execute a keyword trigger."""
    try:
        logger.info(f"Executing keyword trigger {trigger_id} for contact {contact_id}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Get trigger
        trigger = get_trigger(db, trigger_id)
        if not trigger:
            logger.error(f"Trigger {trigger_id} not found")
            return {"success": False, "error": "Trigger not found"}
        
        # Get contact
        from ..flow_engine.crud import get_contact
        contact = get_contact(db, contact_id)
        if not contact:
            logger.error(f"Contact {contact_id} not found")
            return {"success": False, "error": "Contact not found"}
        
        # Execute flow
        engine = FlowEngine(db)
        execution = engine.start_flow(
            flow_id=trigger.flow_id,
            contact_phone=contact.phone_number,
            bot_id=trigger.bot_id,
            initial_state={
                "triggered_by": trigger.name,
                "trigger_type": "keyword",
                "matched_message": matched_message
            }
        )
        
        # Log trigger execution
        create_trigger_log(db, {
            "trigger_id": trigger_id,
            "contact_id": contact_id,
            "execution_id": execution.id,
            "matched_value": matched_message,
            "success": True
        })
        
        # Update trigger last execution time
        trigger.last_triggered_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully executed keyword trigger {trigger_id}")
        return {"success": True, "execution_id": execution.id}
    
    except Exception as e:
        logger.error(f"Failed to execute keyword trigger {trigger_id}: {str(e)}")
        
        # Log failed execution
        try:
            db = next(get_sync_session())
            create_trigger_log(db, {
                "trigger_id": trigger_id,
                "contact_id": contact_id,
                "matched_value": matched_message,
                "success": False,
                "error": str(e)
            })
        except Exception as log_error:
            logger.error(f"Failed to log trigger execution error: {log_error}")
        
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="src.triggers.tasks.execute_event_trigger")
def execute_event_trigger(self, trigger_id: int, contact_id: int, event_context: dict):
    """Execute an event trigger."""
    try:
        logger.info(f"Executing event trigger {trigger_id} for contact {contact_id}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Get trigger
        trigger = get_trigger(db, trigger_id)
        if not trigger:
            logger.error(f"Trigger {trigger_id} not found")
            return {"success": False, "error": "Trigger not found"}
        
        # Get contact
        from ..flow_engine.crud import get_contact
        contact = get_contact(db, contact_id)
        if not contact:
            logger.error(f"Contact {contact_id} not found")
            return {"success": False, "error": "Contact not found"}
        
        # Execute flow
        engine = FlowEngine(db)
        execution = engine.start_flow(
            flow_id=trigger.flow_id,
            contact_phone=contact.phone_number,
            bot_id=trigger.bot_id,
            initial_state={
                "triggered_by": trigger.name,
                "trigger_type": "event",
                "event_context": event_context
            }
        )
        
        # Log trigger execution
        create_trigger_log(db, {
            "trigger_id": trigger_id,
            "contact_id": contact_id,
            "execution_id": execution.id,
            "matched_value": event_context.get("event_type", "unknown"),
            "success": True
        })
        
        # Update trigger last execution time
        trigger.last_triggered_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully executed event trigger {trigger_id}")
        return {"success": True, "execution_id": execution.id}
    
    except Exception as e:
        logger.error(f"Failed to execute event trigger {trigger_id}: {str(e)}")
        
        # Log failed execution
        try:
            db = next(get_sync_session())
            create_trigger_log(db, {
                "trigger_id": trigger_id,
                "contact_id": contact_id,
                "matched_value": event_context.get("event_type", "unknown"),
                "success": False,
                "error": str(e)
            })
        except Exception as log_error:
            logger.error(f"Failed to log trigger execution error: {log_error}")
        
        return {"success": False, "error": str(e)}
