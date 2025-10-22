"""
Flow Engine API router for flow execution management.
"""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..shared.database import get_sync_session
from ..shared.models.bot_builder import Contact, FlowExecution
from ..shared.schemas.flow_engine import (
    ContactSchema, ContactResponse, ContactListResponse,
    FlowExecutionResponse, FlowExecutionListResponse,
    FlowExecutionLogResponse, StartFlowRequest, ResumeFlowRequest,
    CancelFlowRequest, UserInputRequest
)
from ..auth.auth import get_current_active_user_sync
from ..team.permissions import require_permission, Permission, check_bot_ownership_or_admin, is_admin
from ..shared.models.auth import User
from .engine import FlowEngine
from .crud import (
    create_contact, get_contact, get_contact_by_phone, get_all_contacts,
    update_contact, delete_contact, get_flow_execution, get_all_flow_executions,
    get_executions_by_phone, get_execution_logs, get_execution_statistics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["Flow Engine"])


# Contact endpoints
@router.post("/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_endpoint(
    contact: ContactSchema,
    current_user: User = Depends(require_permission(Permission.CONTACT_MANAGE)),
    db: Session = Depends(get_sync_session)
):
    """Create a new contact."""
    # Check if contact already exists
    existing_contact = await asyncio.to_thread(get_contact_by_phone, db, contact.phone_number)
    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact with this phone number already exists")
    
    contact_data = contact.dict()
    # Contacts are shared resources across bots, no direct ownership needed
    new_contact = await asyncio.to_thread(create_contact, db, contact_data)
    return ContactResponse.from_orm(new_contact)


@router.get("/contacts/", response_model=ContactListResponse)
async def get_all_contacts_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_session)
):
    """Get all contacts with pagination."""
    contacts = await asyncio.to_thread(get_all_contacts, db, skip, limit)
    total = await asyncio.to_thread(lambda: db.query(Contact).count())
    
    return ContactListResponse(
        contacts=[ContactResponse.from_orm(contact) for contact in contacts],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact_endpoint(contact_id: int, db: Session = Depends(get_sync_session)):
    """Get a contact by ID."""
    contact = await asyncio.to_thread(get_contact, db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.from_orm(contact)


@router.get("/contacts/phone/{phone_number}", response_model=ContactResponse)
async def get_contact_by_phone_endpoint(phone_number: str, db: Session = Depends(get_sync_session)):
    """Get a contact by phone number."""
    contact = await asyncio.to_thread(get_contact_by_phone, db, phone_number)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.from_orm(contact)


# Flow execution endpoints
@router.post("/execute", response_model=FlowExecutionResponse, status_code=status.HTTP_201_CREATED)
async def start_flow_execution(
    request: StartFlowRequest,
    current_user: User = Depends(require_permission(Permission.FLOW_CREATE)),
    db: Session = Depends(get_sync_session)
):
    """Start a new flow execution."""
    # Verify user owns the bot
    from ..shared.models.bot_builder import Bot
    bot = await asyncio.to_thread(lambda: db.query(Bot).filter(Bot.id == request.bot_id).first())
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not await asyncio.to_thread(check_bot_ownership_or_admin, bot, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied to this bot")
    
    try:
        engine = FlowEngine(db)
        execution = await engine.start_flow(
            flow_id=request.flow_id,
            contact_phone=request.contact_phone,
            bot_id=request.bot_id,
            initial_state=request.initial_state
        )
        return FlowExecutionResponse.from_orm(execution)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start flow execution")


@router.get("/executions/", response_model=FlowExecutionListResponse)
async def get_all_executions_endpoint(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission(Permission.FLOW_READ)),
    db: Session = Depends(get_sync_session)
):
    """Get all flow executions with pagination."""
    # Admins see all executions, users see only executions from their bots
    if await asyncio.to_thread(is_admin, current_user, db):
        executions = await asyncio.to_thread(get_all_flow_executions, db, skip, limit)
        total = await asyncio.to_thread(lambda: db.query(FlowExecution).count())
    else:
        # Filter executions by bot ownership
        from ..shared.models.bot_builder import Bot
        executions = await asyncio.to_thread(
            lambda: db.query(FlowExecution).join(Bot).filter(Bot.created_by_id == current_user.id).offset(skip).limit(limit).all()
        )
        total = await asyncio.to_thread(
            lambda: db.query(FlowExecution).join(Bot).filter(Bot.created_by_id == current_user.id).count()
        )
    
    return FlowExecutionListResponse(
        executions=[FlowExecutionResponse.from_orm(execution) for execution in executions],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/executions/{execution_id}", response_model=FlowExecutionResponse)
async def get_execution_endpoint(
    execution_id: int,
    current_user: User = Depends(require_permission(Permission.FLOW_READ)),
    db: Session = Depends(get_sync_session)
):
    """Get a flow execution by ID."""
    execution = await asyncio.to_thread(get_flow_execution, db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")
    
    # Check ownership through bot
    if not await asyncio.to_thread(check_bot_ownership_or_admin, execution, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied to this execution")
    
    return FlowExecutionResponse.from_orm(execution)


@router.get("/executions/contact/{phone_number}", response_model=FlowExecutionListResponse)
async def get_executions_by_contact_endpoint(
    phone_number: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_sync_session)
):
    """Get flow executions for a specific contact."""
    executions = await asyncio.to_thread(get_executions_by_phone, db, phone_number, skip, limit)
    total = len(executions)  # This is approximate, could be improved with proper counting
    
    return FlowExecutionListResponse(
        executions=[FlowExecutionResponse.from_orm(execution) for execution in executions],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.post("/executions/{execution_id}/resume", response_model=dict)
async def resume_execution_endpoint(
    execution_id: int,
    request: ResumeFlowRequest,
    db: Session = Depends(get_sync_session)
):
    """Manually resume a flow execution."""
    try:
        engine = FlowEngine(db)
        execution = await asyncio.to_thread(get_flow_execution, db, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
        
        result = await engine.resume_execution(execution_id, execution.current_node_index)
        return {"success": True, "result": result.dict()}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resume execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resume execution")


@router.post("/executions/{execution_id}/cancel", response_model=dict)
async def cancel_execution_endpoint(
    execution_id: int,
    request: CancelFlowRequest,
    db: Session = Depends(get_sync_session)
):
    """Cancel a flow execution."""
    try:
        engine = FlowEngine(db)
        execution = await asyncio.to_thread(get_flow_execution, db, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
        
        await engine.fail_execution(execution_id, "Cancelled by user")
        return {"success": True, "message": "Execution cancelled"}
    
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel execution")


@router.post("/executions/{execution_id}/input", response_model=dict)
async def handle_user_input_endpoint(
    execution_id: int,
    request: UserInputRequest,
    db: Session = Depends(get_sync_session)
):
    """Handle user input for a flow execution."""
    try:
        engine = FlowEngine(db)
        execution = await asyncio.to_thread(get_flow_execution, db, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
        
        result = await engine.handle_user_input(
            execution_id=execution_id,
            message=request.message,
            message_type=request.message_type
        )
        return {"success": True, "result": result.dict()}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to handle user input for execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to handle user input")


@router.get("/executions/{execution_id}/logs", response_model=List[FlowExecutionLogResponse])
async def get_execution_logs_endpoint(
    execution_id: int,
    db: Session = Depends(get_sync_session)
):
    """Get execution logs for a flow execution."""
    execution = await asyncio.to_thread(get_flow_execution, db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")
    
    logs = await asyncio.to_thread(get_execution_logs, db, execution_id)
    return [FlowExecutionLogResponse.from_orm(log) for log in logs]


@router.get("/statistics", response_model=dict)
async def get_execution_statistics_endpoint(db: Session = Depends(get_sync_session)):
    """Get flow execution statistics."""
    stats = await asyncio.to_thread(get_execution_statistics, db)
    return stats


# Utility endpoints
@router.post("/test-flow/{flow_id}")
async def test_flow_endpoint(
    flow_id: int,
    test_phone: str = Query(..., description="Test phone number"),
    db: Session = Depends(get_sync_session)
):
    """Test a flow with a test phone number."""
    try:
        engine = FlowEngine(db)
        execution = await engine.start_flow(
            flow_id=flow_id,
            contact_phone=test_phone,
            bot_id=1,  # Default bot ID for testing
            initial_state={"test_mode": True}
        )
        return {"success": True, "execution_id": execution.id}
    
    except Exception as e:
        logger.error(f"Failed to test flow {flow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test flow: {str(e)}")
