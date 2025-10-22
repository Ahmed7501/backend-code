"""
CRUD operations for flow engine functionality.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, and_
from datetime import datetime

from ..shared.models.bot_builder import Contact, FlowExecution, FlowExecutionLog
from ..shared.schemas.flow_engine import (
    ContactSchema, FlowExecutionSchema, FlowExecutionStatus
)


# Contact CRUD operations
def create_contact(db: Session, contact_data: Dict[str, Any]) -> Contact:
    """Create a new contact."""
    contact = Contact(
        phone_number=contact_data["phone_number"],
        first_name=contact_data.get("first_name"),
        last_name=contact_data.get("last_name"),
        meta_data=contact_data.get("meta_data", {})
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contact(db: Session, contact_id: int) -> Optional[Contact]:
    """Get a contact by ID."""
    return db.query(Contact).filter(Contact.id == contact_id).first()


def get_contact_by_phone(db: Session, phone_number: str) -> Optional[Contact]:
    """Get a contact by phone number."""
    return db.query(Contact).filter(Contact.phone_number == phone_number).first()


def get_all_contacts(db: Session, skip: int = 0, limit: int = 100) -> List[Contact]:
    """Get all contacts with pagination."""
    return db.query(Contact).offset(skip).limit(limit).all()


def update_contact(db: Session, contact_id: int, contact_update: Dict[str, Any]) -> Optional[Contact]:
    """Update a contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return None
    
    for field, value in contact_update.items():
        if hasattr(contact, field):
            setattr(contact, field, value)
    
    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: int) -> bool:
    """Delete a contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return False
    
    db.delete(contact)
    db.commit()
    return True


# Flow Execution CRUD operations
def create_flow_execution(db: Session, execution_data: Dict[str, Any]) -> FlowExecution:
    """Create a new flow execution."""
    execution = FlowExecution(
        flow_id=execution_data["flow_id"],
        contact_id=execution_data["contact_id"],
        bot_id=execution_data["bot_id"],
        current_node_index=execution_data.get("current_node_index", 0),
        state=execution_data.get("state", {}),
        status=execution_data.get("status", FlowExecutionStatus.RUNNING)
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def get_flow_execution(db: Session, execution_id: int) -> Optional[FlowExecution]:
    """Get a flow execution by ID with eager-loaded relationships."""
    return db.query(FlowExecution).options(
        selectinload(FlowExecution.flow),
        selectinload(FlowExecution.contact),
        selectinload(FlowExecution.bot)
    ).filter(FlowExecution.id == execution_id).first()


def get_all_flow_executions(db: Session, skip: int = 0, limit: int = 100) -> List[FlowExecution]:
    """Get all flow executions with pagination."""
    return db.query(FlowExecution).order_by(desc(FlowExecution.started_at)).offset(skip).limit(limit).all()


def get_executions_by_contact(db: Session, contact_id: int, skip: int = 0, limit: int = 100) -> List[FlowExecution]:
    """Get flow executions for a specific contact."""
    return (
        db.query(FlowExecution)
        .filter(FlowExecution.contact_id == contact_id)
        .order_by(desc(FlowExecution.started_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_executions_by_phone(db: Session, phone_number: str, skip: int = 0, limit: int = 100) -> List[FlowExecution]:
    """Get flow executions for a specific phone number."""
    return (
        db.query(FlowExecution)
        .join(Contact)
        .filter(Contact.phone_number == phone_number)
        .order_by(desc(FlowExecution.started_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_executions_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[FlowExecution]:
    """Get flow executions by status."""
    return (
        db.query(FlowExecution)
        .filter(FlowExecution.status == status)
        .order_by(desc(FlowExecution.started_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_execution_for_contact(db: Session, contact_id: int) -> Optional[FlowExecution]:
    """Get active execution for a contact."""
    return (
        db.query(FlowExecution)
        .filter(
            and_(
                FlowExecution.contact_id == contact_id,
                FlowExecution.status.in_([FlowExecutionStatus.RUNNING, FlowExecutionStatus.WAITING])
            )
        )
        .order_by(desc(FlowExecution.started_at))
        .first()
    )


def update_flow_execution(db: Session, execution_id: int, execution_update: Dict[str, Any]) -> Optional[FlowExecution]:
    """Update a flow execution."""
    execution = db.query(FlowExecution).filter(FlowExecution.id == execution_id).first()
    if not execution:
        return None
    
    for field, value in execution_update.items():
        if hasattr(execution, field):
            setattr(execution, field, value)
    
    execution.last_executed_at = datetime.utcnow()
    db.commit()
    db.refresh(execution)
    return execution


def delete_flow_execution(db: Session, execution_id: int) -> bool:
    """Delete a flow execution."""
    execution = db.query(FlowExecution).filter(FlowExecution.id == execution_id).first()
    if not execution:
        return False
    
    db.delete(execution)
    db.commit()
    return True


# Flow Execution Log CRUD operations
def create_execution_log(db: Session, log_data: Dict[str, Any]) -> FlowExecutionLog:
    """Create a new execution log entry."""
    log = FlowExecutionLog(
        execution_id=log_data["execution_id"],
        node_index=log_data["node_index"],
        node_type=log_data["node_type"],
        action=log_data["action"],
        result=log_data.get("result"),
        error=log_data.get("error")
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_execution_logs(db: Session, execution_id: int) -> List[FlowExecutionLog]:
    """Get execution logs for a flow execution."""
    return (
        db.query(FlowExecutionLog)
        .filter(FlowExecutionLog.execution_id == execution_id)
        .order_by(FlowExecutionLog.executed_at)
        .all()
    )


def get_execution_log(db: Session, log_id: int) -> Optional[FlowExecutionLog]:
    """Get an execution log by ID."""
    return db.query(FlowExecutionLog).filter(FlowExecutionLog.id == log_id).first()


def delete_execution_logs(db: Session, execution_id: int) -> int:
    """Delete all logs for a flow execution."""
    logs = db.query(FlowExecutionLog).filter(FlowExecutionLog.execution_id == execution_id).all()
    count = len(logs)
    for log in logs:
        db.delete(log)
    db.commit()
    return count


# Utility functions
def get_execution_count_by_status(db: Session, status: str) -> int:
    """Get count of executions by status."""
    return db.query(FlowExecution).filter(FlowExecution.status == status).count()


def get_execution_count_by_contact(db: Session, contact_id: int) -> int:
    """Get count of executions for a contact."""
    return db.query(FlowExecution).filter(FlowExecution.contact_id == contact_id).count()


def get_execution_count_by_bot(db: Session, bot_id: int) -> int:
    """Get count of executions for a bot."""
    return db.query(FlowExecution).filter(FlowExecution.bot_id == bot_id).count()


def get_execution_statistics(db: Session) -> Dict[str, int]:
    """Get execution statistics."""
    return {
        "total_executions": db.query(FlowExecution).count(),
        "running_executions": get_execution_count_by_status(db, FlowExecutionStatus.RUNNING),
        "waiting_executions": get_execution_count_by_status(db, FlowExecutionStatus.WAITING),
        "completed_executions": get_execution_count_by_status(db, FlowExecutionStatus.COMPLETED),
        "failed_executions": get_execution_count_by_status(db, FlowExecutionStatus.FAILED),
        "total_contacts": db.query(Contact).count()
    }
