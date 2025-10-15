"""
Event dispatcher system for firing and handling system events.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .matcher import TriggerMatcher
from .crud import get_active_event_triggers, create_trigger_log
from .tasks import execute_event_trigger
from ..flow_engine.crud import get_contact_by_phone, get_all_contacts

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Service for firing and handling system events."""
    
    def __init__(self, db: Session):
        self.db = db
        self.matcher = TriggerMatcher(db)
    
    async def fire_event(
        self,
        event_type: str,
        bot_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire an event and execute matching triggers."""
        try:
            logger.info(f"Firing event '{event_type}' for bot {bot_id}")
            
            # Get matching event triggers
            triggers = get_active_event_triggers(self.db, bot_id, event_type)
            
            if not triggers:
                logger.info(f"No event triggers found for event '{event_type}' and bot {bot_id}")
                return []
            
            # Execute triggers
            results = []
            for trigger in triggers:
                try:
                    # Check if trigger conditions are met
                    if await self.matcher.match_event_triggers(event_type, bot_id, context):
                        # Execute trigger for all contacts or specific contacts
                        execution_results = await self._execute_event_trigger(
                            trigger, event_type, context
                        )
                        results.extend(execution_results)
                
                except Exception as e:
                    logger.error(f"Failed to execute event trigger {trigger.id}: {str(e)}")
                    # Log failed execution
                    create_trigger_log(self.db, {
                        "trigger_id": trigger.id,
                        "contact_id": 0,  # System event
                        "matched_value": event_type,
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"Event '{event_type}' processed: {len(results)} trigger executions")
            return results
        
        except Exception as e:
            logger.error(f"Failed to fire event '{event_type}': {str(e)}")
            return []
    
    async def _execute_event_trigger(
        self,
        trigger,
        event_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute an event trigger."""
        results = []
        
        try:
            # Determine which contacts to execute for
            contacts = await self._get_contacts_for_event(trigger, event_type, context)
            
            for contact in contacts:
                try:
                    # Execute trigger asynchronously
                    task = execute_event_trigger.delay(
                        trigger.id,
                        contact.id,
                        context or {}
                    )
                    
                    results.append({
                        "trigger_id": trigger.id,
                        "contact_id": contact.id,
                        "task_id": task.id,
                        "success": True
                    })
                    
                    logger.info(f"Scheduled event trigger {trigger.id} for contact {contact.id}")
                
                except Exception as e:
                    logger.error(f"Failed to schedule event trigger for contact {contact.id}: {str(e)}")
                    results.append({
                        "trigger_id": trigger.id,
                        "contact_id": contact.id,
                        "success": False,
                        "error": str(e)
                    })
        
        except Exception as e:
            logger.error(f"Failed to execute event trigger {trigger.id}: {str(e)}")
        
        return results
    
    async def _get_contacts_for_event(
        self,
        trigger,
        event_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List:
        """Get contacts to execute trigger for."""
        try:
            # Check if trigger has specific contact conditions
            event_conditions = trigger.event_conditions or {}
            contact_filter = event_conditions.get("contact_filter", "all")
            
            if contact_filter == "specific":
                # Execute for specific contacts mentioned in context
                contact_ids = context.get("contact_ids", []) if context else []
                if contact_ids:
                    from ..flow_engine.crud import get_contact
                    contacts = [get_contact(self.db, cid) for cid in contact_ids]
                    return [c for c in contacts if c]  # Filter out None values
                return []
            
            elif contact_filter == "new_contacts":
                # Execute for contacts created in last 24 hours
                from datetime import datetime, timedelta
                since = datetime.utcnow() - timedelta(hours=24)
                contacts = (
                    self.db.query(Contact)
                    .filter(Contact.created_at >= since)
                    .all()
                )
                return contacts
            
            elif contact_filter == "active_contacts":
                # Execute for contacts with recent activity
                from datetime import datetime, timedelta
                since = datetime.utcnow() - timedelta(days=7)
                contacts = (
                    self.db.query(Contact)
                    .join(FlowExecution)
                    .filter(FlowExecution.last_executed_at >= since)
                    .distinct()
                    .all()
                )
                return contacts
            
            else:
                # Execute for all contacts
                return get_all_contacts(self.db, limit=1000)
        
        except Exception as e:
            logger.error(f"Failed to get contacts for event: {str(e)}")
            return []
    
    async def fire_new_contact_event(
        self,
        bot_id: int,
        contact_id: int,
        contact_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire new contact event."""
        context = {
            "contact_id": contact_id,
            "contact_data": contact_data or {},
            "event_source": "contact_creation"
        }
        return await self.fire_event("new_contact", bot_id, context)
    
    async def fire_message_received_event(
        self,
        bot_id: int,
        contact_id: int,
        message_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire message received event."""
        context = {
            "contact_id": contact_id,
            "message_data": message_data or {},
            "event_source": "message_received"
        }
        return await self.fire_event("message_received", bot_id, context)
    
    async def fire_flow_completed_event(
        self,
        bot_id: int,
        contact_id: int,
        flow_id: int,
        execution_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire flow completed event."""
        context = {
            "contact_id": contact_id,
            "flow_id": flow_id,
            "execution_data": execution_data or {},
            "event_source": "flow_completed"
        }
        return await self.fire_event("flow_completed", bot_id, context)
    
    async def fire_flow_failed_event(
        self,
        bot_id: int,
        contact_id: int,
        flow_id: int,
        error_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire flow failed event."""
        context = {
            "contact_id": contact_id,
            "flow_id": flow_id,
            "error_data": error_data or {},
            "event_source": "flow_failed"
        }
        return await self.fire_event("flow_failed", bot_id, context)
    
    async def fire_opt_in_event(
        self,
        bot_id: int,
        contact_id: int,
        opt_in_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire opt-in event."""
        context = {
            "contact_id": contact_id,
            "opt_in_data": opt_in_data or {},
            "event_source": "opt_in"
        }
        return await self.fire_event("opt_in", bot_id, context)
    
    async def fire_opt_out_event(
        self,
        bot_id: int,
        contact_id: int,
        opt_out_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fire opt-out event."""
        context = {
            "contact_id": contact_id,
            "opt_out_data": opt_out_data or {},
            "event_source": "opt_out"
        }
        return await self.fire_event("opt_out", bot_id, context)


# Global event dispatcher instance
_event_dispatcher = None


def get_event_dispatcher(db: Session) -> EventDispatcher:
    """Get global event dispatcher instance."""
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = EventDispatcher(db)
    return _event_dispatcher
