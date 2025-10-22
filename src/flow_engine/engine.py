"""
Core Flow Engine for executing conversation flows.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..shared.models.bot_builder import (
    Bot, BotFlow, Contact, FlowExecution, FlowExecutionLog
)
from ..shared.schemas.flow_engine import (
    FlowExecutionStatus, NodeExecutionResult, FlowNodeSchema
)
from .flow_normalizer import FlowNormalizer
from .node_executors import NodeExecutorFactory
from .crud import (
    create_contact, get_contact_by_phone, get_flow_execution,
    create_flow_execution, update_flow_execution, create_execution_log,
    get_active_execution_for_contact
)

logger = logging.getLogger(__name__)


class FlowEngine:
    """Core flow execution engine."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def start_flow(
        self,
        flow_id: int,
        contact_phone: str,
        bot_id: int,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> FlowExecution:
        """Start a new flow execution."""
        try:
            # Get or create contact
            contact = await asyncio.to_thread(get_contact_by_phone, self.db, contact_phone)
            if not contact:
                contact = await asyncio.to_thread(create_contact, self.db, {
                    "phone_number": contact_phone,
                    "meta_data": {}
                })
            
            # Check if contact already has an active execution
            active_execution = await asyncio.to_thread(get_active_execution_for_contact, self.db, contact.id)
            if active_execution:
                logger.info(f"Contact {contact_phone} already has active execution {active_execution.id}")
                return active_execution
            
            # Get flow
            flow = await asyncio.to_thread(lambda: self.db.query(BotFlow).filter(BotFlow.id == flow_id).first())
            if not flow:
                raise ValueError(f"Flow {flow_id} not found")
            
            # Get bot
            bot = await asyncio.to_thread(lambda: self.db.query(Bot).filter(Bot.id == bot_id).first())
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")
            
            # Create flow execution
            execution = await asyncio.to_thread(create_flow_execution, self.db, {
                "flow_id": flow_id,
                "contact_id": contact.id,
                "bot_id": bot_id,
                "current_node_index": 0,
                "state": initial_state or {},
                "status": FlowExecutionStatus.RUNNING
            })
            
            logger.info(f"Started flow execution {execution.id} for contact {contact_phone}")
            
            # Start executing from first node
            await self._execute_current_node(execution)
            
            return execution
        
        except Exception as e:
            logger.error(f"Failed to start flow {flow_id} for contact {contact_phone}: {str(e)}")
            raise
    
    async def execute_node(self, execution_id: int, node_index: int) -> NodeExecutionResult:
        """Execute a specific node in a flow execution."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            # Update current node index
            execution.current_node_index = node_index
            execution.last_executed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Execute the node
            result = await self._execute_current_node(execution)
            return result
        
        except Exception as e:
            logger.error(f"Failed to execute node {node_index} for execution {execution_id}: {str(e)}")
            await self.fail_execution(execution_id, str(e))
            raise
    
    async def resume_execution(self, execution_id: int, next_node_index: int) -> NodeExecutionResult:
        """Resume flow execution after wait or delay."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            if execution.status != FlowExecutionStatus.WAITING:
                logger.warning(f"Execution {execution_id} is not in waiting status: {execution.status}")
            
            # Update status to running
            execution.status = FlowExecutionStatus.RUNNING
            execution.current_node_index = next_node_index
            execution.last_executed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Continue execution
            result = await self._execute_current_node(execution)
            return result
        
        except Exception as e:
            logger.error(f"Failed to resume execution {execution_id}: {str(e)}")
            await self.fail_execution(execution_id, str(e))
            raise
    
    async def handle_user_input(
        self,
        execution_id: int,
        message: str,
        message_type: str = "text"
    ) -> NodeExecutionResult:
        """Handle user input for a flow execution."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            # Store user input in state
            execution.state["user_response"] = message
            execution.state["user_response_type"] = message_type
            execution.state["last_user_input_at"] = datetime.utcnow().isoformat()
            
            # Update last executed time
            execution.last_executed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Continue execution from current node
            result = await self._execute_current_node(execution)
            return result
        
        except Exception as e:
            logger.error(f"Failed to handle user input for execution {execution_id}: {str(e)}")
            await self.fail_execution(execution_id, str(e))
            raise
    
    async def complete_execution(self, execution_id: int) -> None:
        """Mark flow execution as completed."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            execution.status = FlowExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.last_executed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            logger.info(f"Completed flow execution {execution_id}")
        
        except Exception as e:
            logger.error(f"Failed to complete execution {execution_id}: {str(e)}")
            raise
    
    async def fail_execution(self, execution_id: int, error: str) -> None:
        """Mark flow execution as failed."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            execution.status = FlowExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.last_executed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Log the error
            await asyncio.to_thread(create_execution_log, self.db, {
                "execution_id": execution_id,
                "node_index": execution.current_node_index,
                "node_type": "error",
                "action": "failed",
                "error": error
            })
            
            logger.error(f"Failed flow execution {execution_id}: {error}")
        
        except Exception as e:
            logger.error(f"Failed to mark execution {execution_id} as failed: {str(e)}")
            raise
    
    async def _execute_current_node(self, execution: FlowExecution) -> NodeExecutionResult:
        """Execute the current node in the flow."""
        try:
            # Get flow structure
            flow = execution.flow
            if not flow or not flow.structure:
                await self.complete_execution(execution.id)
                return NodeExecutionResult(success=True, next_node_index=None)
            
            # Normalize flow structure for backward compatibility
            normalized_structure = FlowNormalizer.normalize_flow_structure(flow.structure)
            
            # Check if we've reached the end of the flow
            if execution.current_node_index >= len(normalized_structure):
                await self.complete_execution(execution.id)
                return NodeExecutionResult(success=True, next_node_index=None)
            
            # Get current node from normalized structure
            node_data = normalized_structure[execution.current_node_index]
            node_type = node_data.get("type")

            # Strict validation - fail fast on invalid data
            if not node_type:
                error_msg = f"Node at index {execution.current_node_index} has no type field. Flow data is corrupted."
                logger.error(error_msg)
                await self.fail_execution(execution.id, error_msg)
                raise ValueError(error_msg)

            node_config = node_data.get("config")
            if not node_config:
                error_msg = f"Node at index {execution.current_node_index} has no config field. Flow data is corrupted."
                logger.error(error_msg)
                await self.fail_execution(execution.id, error_msg)
                raise ValueError(error_msg)
            
            # Get contact and bot
            contact = execution.contact
            bot = execution.bot
            
            # Create executor and execute node
            executor = await asyncio.to_thread(NodeExecutorFactory.get_executor, node_type, self.db)
            
            if node_type == "send_message":
                from ..shared.schemas.flow_engine import SendMessageNodeConfig
                config = SendMessageNodeConfig(**node_config)
                result = await executor.execute(config, execution, contact, bot)
            
            elif node_type == "wait":
                from ..shared.schemas.flow_engine import WaitNodeConfig
                config = WaitNodeConfig(**node_config)
                result = await asyncio.to_thread(executor.execute, config, execution, contact, bot)
            
            elif node_type == "condition":
                from ..shared.schemas.flow_engine import ConditionNodeConfig
                config = ConditionNodeConfig(**node_config)
                result = await asyncio.to_thread(executor.execute, config, execution, contact, bot)
            
            elif node_type == "webhook_action":
                from ..shared.schemas.flow_engine import WebhookActionNodeConfig
                config = WebhookActionNodeConfig(**node_config)
                result = await executor.execute(config, execution, contact, bot)
            
            elif node_type == "set_attribute":
                from ..shared.schemas.flow_engine import SetAttributeNodeConfig
                config = SetAttributeNodeConfig(**node_config)
                result = await asyncio.to_thread(executor.execute, config, execution, contact, bot)
            
            else:
                raise ValueError(f"Unknown node type: {node_type}")
            
            # Log execution
            await asyncio.to_thread(create_execution_log, self.db, {
                "execution_id": execution.id,
                "node_index": execution.current_node_index,
                "node_type": node_type,
                "action": "executed" if result.success else "failed",
                "result": result.result_data,
                "error": result.error
            })
            
            # Handle result
            if result.success:
                if result.next_node_index is not None:
                    # Move to next node
                    execution.current_node_index = result.next_node_index
                    execution.last_executed_at = datetime.utcnow()
                    
                    if result.scheduled_task_id:
                        # Node scheduled a task (e.g., wait node)
                        execution.status = FlowExecutionStatus.WAITING
                    
                    await asyncio.to_thread(self.db.commit)
                    
                    # Continue execution if not waiting
                    if execution.status == FlowExecutionStatus.RUNNING:
                        return await self._execute_current_node(execution)
                else:
                    # Flow completed
                    await self.complete_execution(execution.id)
            else:
                # Node execution failed
                await self.fail_execution(execution.id, result.error or "Unknown error")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to execute current node for execution {execution.id}: {str(e)}")
            await self.fail_execution(execution.id, str(e))
            raise
    
    async def execute_webhook_action(self, execution_id: int, webhook_config: dict) -> NodeExecutionResult:
        """Execute webhook action asynchronously."""
        try:
            execution = await asyncio.to_thread(get_flow_execution, self.db, execution_id)
            if not execution:
                raise ValueError(f"Flow execution {execution_id} not found")
            
            # Create webhook executor
            from .node_executors import WebhookActionNodeExecutor
            from ..shared.schemas.flow_engine import WebhookActionNodeConfig
            
            executor = await asyncio.to_thread(WebhookActionNodeExecutor, self.db)
            config = WebhookActionNodeConfig(**webhook_config)
            
            result = await executor.execute(config, execution, execution.contact, execution.bot)
            
            # Update execution state with webhook result
            if result.success and result.result_data:
                execution.state.update(result.result_data)
                execution.last_executed_at = datetime.utcnow()
                await asyncio.to_thread(self.db.commit)
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to execute webhook action for execution {execution_id}: {str(e)}")
            raise
