"""
Node executors for different flow node types.
"""

import logging
import httpx
import re
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

from ..shared.schemas.flow_engine import (
    SendMessageNodeConfig,
    WaitNodeConfig,
    ConditionNodeConfig,
    WebhookActionNodeConfig,
    SetAttributeNodeConfig,
    NodeExecutionResult
)
from ..whatsapp.service import whatsapp_service
from ..shared.models.bot_builder import Bot, Contact, FlowExecution

logger = logging.getLogger(__name__)


class BaseNodeExecutor:
    """Base class for node executors."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def interpolate_variables(self, content: str, state: Dict[str, Any], contact: Contact) -> str:
        """Interpolate variables in content using {{variable}} syntax."""
        def replace_var(match):
            var_path = match.group(1)
            try:
                if var_path.startswith("contact."):
                    field = var_path.split(".", 1)[1]
                    
                    # Handle contact attributes
                    if field.startswith("attribute."):
                        attr_key = field.split(".", 1)[1]
                        # Load attributes from database if not already loaded
                        if not hasattr(contact, 'attributes_dict'):
                            from .contact_crud import get_contact_attributes_dict
                            contact.attributes_dict = get_contact_attributes_dict(self.db, contact.id)
                        return str(contact.attributes_dict.get(attr_key, ""))
                    else:
                        # Handle regular contact fields
                        return str(getattr(contact, field, ""))
                        
                elif var_path.startswith("state."):
                    field = var_path.split(".", 1)[1]
                    return str(state.get(field, ""))
                else:
                    return str(state.get(var_path, ""))
            except Exception as e:
                logger.warning(f"Failed to interpolate variable {var_path}: {e}")
                return match.group(0)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, content)


class SendMessageNodeExecutor(BaseNodeExecutor):
    """Executor for send_message nodes."""
    
    async def execute(
        self,
        config: SendMessageNodeConfig,
        execution: FlowExecution,
        contact: Contact,
        bot: Bot
    ) -> NodeExecutionResult:
        """Execute send_message node."""
        try:
            # Interpolate variables in content
            interpolated_content = {}
            for key, value in config.content.items():
                if isinstance(value, str):
                    interpolated_content[key] = self.interpolate_variables(value, execution.state, contact)
                else:
                    interpolated_content[key] = value
            
            # Get WhatsApp credentials
            credentials = await whatsapp_service.get_credentials(bot)
            
            # Send message based on type
            if config.message_type == "text":
                from ..shared.schemas.whatsapp import WhatsAppTextMessage
                message = WhatsAppTextMessage(
                    to=contact.phone_number,
                    text=interpolated_content.get("text", "")
                )
                response = await whatsapp_service.send_text_message(credentials, message)
            
            elif config.message_type == "template":
                from ..shared.schemas.whatsapp import WhatsAppTemplateMessage
                message = WhatsAppTemplateMessage(
                    to=contact.phone_number,
                    template_name=interpolated_content.get("template_name", ""),
                    language_code=interpolated_content.get("language_code", "en_US"),
                    parameters=interpolated_content.get("parameters", [])
                )
                response = await whatsapp_service.send_template_message(credentials, message)
            
            elif config.message_type == "media":
                from ..shared.schemas.whatsapp import WhatsAppMediaMessage
                message = WhatsAppMediaMessage(
                    to=contact.phone_number,
                    media_type=interpolated_content.get("media_type", "image"),
                    media_url=interpolated_content.get("media_url"),
                    media_id=interpolated_content.get("media_id"),
                    caption=interpolated_content.get("caption")
                )
                response = await whatsapp_service.send_media_message(credentials, message)
            
            elif config.message_type == "interactive":
                from ..shared.schemas.whatsapp import WhatsAppInteractiveMessage
                message = WhatsAppInteractiveMessage(
                    to=contact.phone_number,
                    interactive_type=interpolated_content.get("interactive_type", "button"),
                    header=interpolated_content.get("header"),
                    body=interpolated_content.get("body", {}),
                    footer=interpolated_content.get("footer"),
                    action=interpolated_content.get("action", {})
                )
                response = await whatsapp_service.send_interactive_message(credentials, message)
            
            else:
                raise ValueError(f"Unsupported message type: {config.message_type}")
            
            return NodeExecutionResult(
                success=True,
                next_node_index=config.next,
                result_data={"response": response}
            )
        
        except Exception as e:
            logger.error(f"Failed to execute send_message node: {str(e)}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )


class WaitNodeExecutor(BaseNodeExecutor):
    """Executor for wait nodes."""
    
    def execute(
        self,
        config: WaitNodeConfig,
        execution: FlowExecution,
        contact: Contact,
        bot: Bot
    ) -> NodeExecutionResult:
        """Execute wait node."""
        try:
            # Calculate wait duration in seconds
            duration_seconds = self._calculate_duration(config.duration, config.unit)
            
            # Schedule Celery task to resume execution
            from .tasks import resume_flow_after_wait
            task = resume_flow_after_wait.apply_async(
                args=[execution.id, config.next],
                countdown=duration_seconds
            )
            
            return NodeExecutionResult(
                success=True,
                next_node_index=None,  # Will be resumed by Celery task
                scheduled_task_id=task.id,
                result_data={"wait_duration": duration_seconds}
            )
        
        except Exception as e:
            logger.error(f"Failed to execute wait node: {str(e)}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )
    
    def _calculate_duration(self, duration: int, unit: str) -> int:
        """Calculate duration in seconds."""
        unit_multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }
        
        multiplier = unit_multipliers.get(unit, 1)
        return duration * multiplier


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executor for condition nodes."""
    
    def execute(
        self,
        config: ConditionNodeConfig,
        execution: FlowExecution,
        contact: Contact,
        bot: Bot
    ) -> NodeExecutionResult:
        """Execute condition node."""
        try:
            # Get variable value
            variable_value = self._get_variable_value(config.variable, execution.state, contact)
            
            # Evaluate condition
            condition_result = self._evaluate_condition(
                variable_value,
                config.operator,
                config.value
            )
            
            # Determine next node
            next_node = config.true_path if condition_result else config.false_path
            
            return NodeExecutionResult(
                success=True,
                next_node_index=next_node,
                result_data={
                    "variable_value": variable_value,
                    "condition_result": condition_result,
                    "operator": config.operator,
                    "comparison_value": config.value
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to execute condition node: {str(e)}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )
    
    def _get_variable_value(self, variable_path: str, state: Dict[str, Any], contact: Contact) -> Any:
        """Get variable value from state or contact."""
        if variable_path.startswith("contact."):
            field = variable_path.split(".", 1)[1]
            return getattr(contact, field, None)
        elif variable_path.startswith("state."):
            field = variable_path.split(".", 1)[1]
            return state.get(field)
        else:
            return state.get(variable_path)
    
    def _evaluate_condition(self, variable_value: Any, operator: str, comparison_value: Any) -> bool:
        """Evaluate condition based on operator."""
        try:
            if operator == "==":
                return variable_value == comparison_value
            elif operator == "!=":
                return variable_value != comparison_value
            elif operator == ">":
                return variable_value > comparison_value
            elif operator == "<":
                return variable_value < comparison_value
            elif operator == ">=":
                return variable_value >= comparison_value
            elif operator == "<=":
                return variable_value <= comparison_value
            elif operator == "contains":
                return str(comparison_value) in str(variable_value)
            elif operator == "starts_with":
                return str(variable_value).startswith(str(comparison_value))
            elif operator == "ends_with":
                return str(variable_value).endswith(str(comparison_value))
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        except Exception as e:
            logger.warning(f"Failed to evaluate condition: {e}")
            return False


class WebhookActionNodeExecutor(BaseNodeExecutor):
    """Executor for webhook_action nodes."""
    
    async def execute(
        self,
        config: WebhookActionNodeConfig,
        execution: FlowExecution,
        contact: Contact,
        bot: Bot
    ) -> NodeExecutionResult:
        """Execute webhook_action node."""
        try:
            # Interpolate variables in URL, headers, and body
            interpolated_url = self.interpolate_variables(config.url, execution.state, contact)
            
            interpolated_headers = {}
            for key, value in config.headers.items():
                interpolated_headers[key] = self.interpolate_variables(str(value), execution.state, contact)
            
            interpolated_body = {}
            for key, value in config.body.items():
                if isinstance(value, str):
                    interpolated_body[key] = self.interpolate_variables(value, execution.state, contact)
                else:
                    interpolated_body[key] = value
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=config.method,
                    url=interpolated_url,
                    headers=interpolated_headers,
                    json=interpolated_body if config.method in ["POST", "PUT", "PATCH"] else None
                )
                
                response_data = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
            
            # Store response in state if specified
            result_data = {"webhook_response": response_data}
            if config.store_response_in:
                execution.state[config.store_response_in] = response_data
            
            return NodeExecutionResult(
                success=True,
                next_node_index=config.next,
                result_data=result_data
            )
        
        except Exception as e:
            logger.error(f"Failed to execute webhook_action node: {str(e)}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )


class SetAttributeNodeExecutor(BaseNodeExecutor):
    """Executor for set_attribute nodes."""
    
    def execute(self, config: SetAttributeNodeConfig, execution: FlowExecution, contact: Contact, bot: Bot) -> NodeExecutionResult:
        """Execute set_attribute node."""
        try:
            # Import here to avoid circular imports
            from .contact_crud import set_contact_attribute
            
            # Interpolate value with variables
            interpolated_value = self.interpolate_variables(
                config.attribute_value, 
                execution.state, 
                contact
            )
            
            # Set attribute in database
            attr = set_contact_attribute(
                self.db,
                contact.id,
                config.attribute_key,
                interpolated_value,
                config.value_type
            )
            
            # Also store in execution state for immediate use
            execution.state[f"contact.{config.attribute_key}"] = interpolated_value
            
            logger.info(f"Set attribute '{config.attribute_key}' = '{interpolated_value}' for contact {contact.id}")
            
            return NodeExecutionResult(
                success=True,
                next_node_index=config.next,
                result_data={
                    "attribute_set": config.attribute_key,
                    "attribute_value": interpolated_value,
                    "value_type": config.value_type
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to execute set_attribute node: {e}")
            return NodeExecutionResult(
                success=False,
                next_node_index=None,
                error=str(e)
            )


class NodeExecutorFactory:
    """Factory for creating node executors."""
    
    @staticmethod
    def get_executor(node_type: str, db_session):
        """Get executor for node type."""
        executors = {
            "send_message": SendMessageNodeExecutor,
            "wait": WaitNodeExecutor,
            "condition": ConditionNodeExecutor,
            "webhook_action": WebhookActionNodeExecutor,
            "set_attribute": SetAttributeNodeExecutor
        }
        
        executor_class = executors.get(node_type)
        if not executor_class:
            raise ValueError(f"Unknown node type: {node_type}")
        
        return executor_class(db_session)
