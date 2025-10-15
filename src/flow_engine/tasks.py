"""
Celery tasks for flow engine async operations.
"""

import logging
from datetime import datetime, timedelta
from celery import current_task
from sqlalchemy.orm import Session

from .celery_app import celery_app
from .engine import FlowEngine
from ..shared.database import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="src.flow_engine.tasks.resume_flow_after_wait")
def resume_flow_after_wait(self, execution_id: int, next_node_index: int):
    """Resume flow execution after wait period."""
    try:
        logger.info(f"Resuming flow execution {execution_id} after wait")
        
        # Get database session
        db = next(get_sync_session())
        
        # Create flow engine and resume execution
        engine = FlowEngine(db)
        result = engine.resume_execution(execution_id, next_node_index)
        
        logger.info(f"Successfully resumed flow execution {execution_id}")
        return {"success": True, "result": result}
    
    except Exception as e:
        logger.error(f"Failed to resume flow execution {execution_id}: {str(e)}")
        
        # Update execution status to failed
        try:
            db = next(get_sync_session())
            engine = FlowEngine(db)
            engine.fail_execution(execution_id, str(e))
        except Exception as update_error:
            logger.error(f"Failed to update execution status: {update_error}")
        
        # Retry the task if it's a temporary error
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying resume_flow_after_wait task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="src.flow_engine.tasks.execute_webhook_action")
def execute_webhook_action(self, execution_id: int, webhook_config: dict):
    """Execute webhook action asynchronously."""
    try:
        logger.info(f"Executing webhook action for execution {execution_id}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Create flow engine and execute webhook
        engine = FlowEngine(db)
        result = engine.execute_webhook_action(execution_id, webhook_config)
        
        logger.info(f"Successfully executed webhook action for execution {execution_id}")
        return {"success": True, "result": result}
    
    except Exception as e:
        logger.error(f"Failed to execute webhook action for execution {execution_id}: {str(e)}")
        
        # Retry the task if it's a temporary error
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying execute_webhook_action task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.flow_engine.tasks.cleanup_old_executions")
def cleanup_old_executions():
    """Clean up old completed and failed flow executions."""
    try:
        logger.info("Starting cleanup of old flow executions")
        
        # Get database session
        db = next(get_sync_session())
        
        from ..shared.models.bot_builder import FlowExecution
        from datetime import datetime, timedelta
        
        # Clean up executions older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_executions = db.query(FlowExecution).filter(
            FlowExecution.status.in_(["completed", "failed"]),
            FlowExecution.completed_at < cutoff_date
        ).all()
        
        count = len(old_executions)
        for execution in old_executions:
            db.delete(execution)
        
        db.commit()
        
        logger.info(f"Cleaned up {count} old flow executions")
        return {"success": True, "cleaned_count": count}
    
    except Exception as e:
        logger.error(f"Failed to cleanup old executions: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True, name="src.flow_engine.tasks.process_incoming_message")
def process_incoming_message(self, execution_id: int, message: str, message_type: str = "text"):
    """Process incoming message for a flow execution."""
    try:
        logger.info(f"Processing incoming message for execution {execution_id}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Create flow engine and handle user input
        engine = FlowEngine(db)
        result = engine.handle_user_input(execution_id, message, message_type)
        
        logger.info(f"Successfully processed incoming message for execution {execution_id}")
        return {"success": True, "result": result}
    
    except Exception as e:
        logger.error(f"Failed to process incoming message for execution {execution_id}: {str(e)}")
        
        # Retry the task if it's a temporary error
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying process_incoming_message task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.flow_engine.tasks.monitor_execution_timeouts")
def monitor_execution_timeouts():
    """Monitor and timeout long-running executions."""
    try:
        logger.info("Monitoring execution timeouts")
        
        # Get database session
        db = next(get_sync_session())
        
        from ..shared.models.bot_builder import FlowExecution
        from datetime import datetime, timedelta
        
        # Find executions running longer than 30 minutes
        timeout_threshold = datetime.utcnow() - timedelta(minutes=30)
        
        timeout_executions = db.query(FlowExecution).filter(
            FlowExecution.status.in_(["running", "waiting"]),
            FlowExecution.last_executed_at < timeout_threshold
        ).all()
        
        count = 0
        for execution in timeout_executions:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            count += 1
        
        db.commit()
        
        logger.info(f"Timed out {count} long-running executions")
        return {"success": True, "timeout_count": count}
    
    except Exception as e:
        logger.error(f"Failed to monitor execution timeouts: {str(e)}")
        return {"success": False, "error": str(e)}
