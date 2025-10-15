"""
Trigger matcher service for matching messages and events against triggers.
"""

import re
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..shared.models.bot_builder import Trigger
from ..shared.schemas.triggers import MatchType, EventType

logger = logging.getLogger(__name__)


class TriggerMatcher:
    """Service for matching triggers against messages and events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def match_keyword_triggers(
        self,
        message: str,
        bot_id: int,
        contact_id: Optional[int] = None
    ) -> Optional[Trigger]:
        """Match message against keyword triggers."""
        try:
            # Get active keyword triggers for bot, ordered by priority
            triggers = (
                self.db.query(Trigger)
                .filter(
                    Trigger.bot_id == bot_id,
                    Trigger.trigger_type == "keyword",
                    Trigger.is_active == True
                )
                .order_by(Trigger.priority.desc())
                .all()
            )
            
            for trigger in triggers:
                if await self._check_keyword_match(
                    message,
                    trigger.keywords,
                    trigger.match_type,
                    trigger.case_sensitive
                ):
                    logger.info(f"Keyword trigger '{trigger.name}' matched for message: {message}")
                    return trigger
            
            return None
        
        except Exception as e:
            logger.error(f"Error matching keyword triggers: {str(e)}")
            return None
    
    async def match_event_triggers(
        self,
        event_type: str,
        bot_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Trigger]:
        """Match event against event triggers."""
        try:
            # Get active event triggers for bot and event type
            triggers = (
                self.db.query(Trigger)
                .filter(
                    Trigger.bot_id == bot_id,
                    Trigger.trigger_type == "event",
                    Trigger.event_type == event_type,
                    Trigger.is_active == True
                )
                .order_by(Trigger.priority.desc())
                .all()
            )
            
            matched_triggers = []
            for trigger in triggers:
                if await self._check_event_conditions(
                    trigger.event_conditions or {},
                    context or {}
                ):
                    matched_triggers.append(trigger)
                    logger.info(f"Event trigger '{trigger.name}' matched for event: {event_type}")
            
            return matched_triggers
        
        except Exception as e:
            logger.error(f"Error matching event triggers: {str(e)}")
            return []
    
    async def _check_keyword_match(
        self,
        message: str,
        keywords: List[str],
        match_type: str,
        case_sensitive: bool
    ) -> bool:
        """Check if message matches any keyword based on match type."""
        if not keywords or not message:
            return False
        
        # Normalize case if not case sensitive
        if not case_sensitive:
            message = message.lower()
            keywords = [kw.lower() for kw in keywords]
        
        try:
            for keyword in keywords:
                if match_type == MatchType.EXACT:
                    if message == keyword:
                        return True
                
                elif match_type == MatchType.CONTAINS:
                    if keyword in message:
                        return True
                
                elif match_type == MatchType.STARTS_WITH:
                    if message.startswith(keyword):
                        return True
                
                elif match_type == MatchType.ENDS_WITH:
                    if message.endswith(keyword):
                        return True
                
                elif match_type == MatchType.REGEX:
                    try:
                        if re.search(keyword, message):
                            return True
                    except re.error as regex_error:
                        logger.warning(f"Invalid regex pattern '{keyword}': {regex_error}")
                        continue
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking keyword match: {str(e)}")
            return False
    
    async def _check_event_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if event conditions are met."""
        if not conditions:
            return True
        
        try:
            for key, expected_value in conditions.items():
                actual_value = context.get(key)
                
                # Handle different comparison types
                if isinstance(expected_value, dict):
                    # Complex condition with operator
                    operator = expected_value.get("operator", "==")
                    value = expected_value.get("value")
                    
                    if not self._evaluate_condition(actual_value, operator, value):
                        return False
                else:
                    # Simple equality check
                    if actual_value != expected_value:
                        return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking event conditions: {str(e)}")
            return False
    
    def _evaluate_condition(
        self,
        actual_value: Any,
        operator: str,
        expected_value: Any
    ) -> bool:
        """Evaluate a single condition."""
        try:
            if operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            elif operator == ">":
                return actual_value > expected_value
            elif operator == "<":
                return actual_value < expected_value
            elif operator == ">=":
                return actual_value >= expected_value
            elif operator == "<=":
                return actual_value <= expected_value
            elif operator == "contains":
                return str(expected_value) in str(actual_value)
            elif operator == "in":
                return actual_value in expected_value
            elif operator == "not_in":
                return actual_value not in expected_value
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    async def test_keyword_trigger(
        self,
        trigger: Trigger,
        test_message: str
    ) -> Dict[str, Any]:
        """Test a keyword trigger against a message."""
        try:
            matched = await self._check_keyword_match(
                test_message,
                trigger.keywords or [],
                trigger.match_type or MatchType.CONTAINS,
                trigger.case_sensitive or False
            )
            
            matched_value = None
            if matched and trigger.keywords:
                # Find which keyword matched
                for keyword in trigger.keywords:
                    if await self._check_keyword_match(
                        test_message,
                        [keyword],
                        trigger.match_type or MatchType.CONTAINS,
                        trigger.case_sensitive or False
                    ):
                        matched_value = keyword
                        break
            
            return {
                "matched": matched,
                "matched_value": matched_value,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error testing keyword trigger: {str(e)}")
            return {
                "matched": False,
                "matched_value": None,
                "error": str(e)
            }
    
    async def test_event_trigger(
        self,
        trigger: Trigger,
        test_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test an event trigger against event data."""
        try:
            matched = await self._check_event_conditions(
                trigger.event_conditions or {},
                test_event
            )
            
            return {
                "matched": matched,
                "matched_value": test_event.get("event_type"),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error testing event trigger: {str(e)}")
            return {
                "matched": False,
                "matched_value": None,
                "error": str(e)
            }
