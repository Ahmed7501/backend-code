"""
Bot Builder router for WhatsApp bot management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..shared.database import get_sync_session
from ..shared.models.bot_builder import Bot, BotFlow, BotNode, Template
from ..shared.schemas.bot_builder import BotSchema, FlowSchema, NodeSchema, TemplateSchema
from .crud import (
    create_bot,
    get_bot,
    get_all_bots,
    update_bot,
    delete_bot,
    create_flow,
    get_flow,
    get_all_flows,
    create_node,
    get_node,
    get_all_nodes,
    create_template,
    get_template,
    get_all_templates
)

router = APIRouter(prefix="/bots", tags=["Bot Builder"])


# Bot endpoints
@router.post("/", response_model=BotSchema, status_code=status.HTTP_201_CREATED)
def create_bot_endpoint(bot: BotSchema, db: Session = Depends(get_sync_session)):
    """Create a new bot."""
    return create_bot(db=db, bot=bot)


@router.get("/", response_model=List[BotSchema])
def get_all_bots_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_sync_session)
):
    """Get all bots with pagination."""
    return get_all_bots(db=db, skip=skip, limit=limit)


@router.get("/{bot_id}", response_model=BotSchema)
def get_bot_endpoint(bot_id: int, db: Session = Depends(get_sync_session)):
    """Get a bot by ID."""
    bot = get_bot(db=db, bot_id=bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.put("/{bot_id}", response_model=BotSchema)
def update_bot_endpoint(
    bot_id: int, 
    bot_update: dict, 
    db: Session = Depends(get_sync_session)
):
    """Update a bot."""
    bot = update_bot(db=db, bot_id=bot_id, bot_update=bot_update)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.delete("/{bot_id}")
def delete_bot_endpoint(bot_id: int, db: Session = Depends(get_sync_session)):
    """Delete a bot."""
    success = delete_bot(db=db, bot_id=bot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": "Bot deleted successfully"}


# Flow endpoints
@router.post("/flows/", response_model=FlowSchema, status_code=status.HTTP_201_CREATED)
def create_flow_endpoint(flow: FlowSchema, db: Session = Depends(get_sync_session)):
    """Create a new flow."""
    return create_flow(db=db, flow=flow)


@router.get("/flows/", response_model=List[FlowSchema])
def get_all_flows_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_sync_session)
):
    """Get all flows with pagination."""
    return get_all_flows(db=db, skip=skip, limit=limit)


@router.get("/flows/{flow_id}", response_model=FlowSchema)
def get_flow_endpoint(flow_id: int, db: Session = Depends(get_sync_session)):
    """Get a flow by ID."""
    flow = get_flow(db=db, flow_id=flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


# Node endpoints
@router.post("/nodes/", response_model=NodeSchema, status_code=status.HTTP_201_CREATED)
def create_node_endpoint(
    node: NodeSchema, 
    flow_id: int, 
    db: Session = Depends(get_sync_session)
):
    """Create a new node."""
    return create_node(db=db, node=node, flow_id=flow_id)


@router.get("/nodes/", response_model=List[NodeSchema])
def get_all_nodes_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_sync_session)
):
    """Get all nodes with pagination."""
    return get_all_nodes(db=db, skip=skip, limit=limit)


@router.get("/nodes/{node_id}", response_model=NodeSchema)
def get_node_endpoint(node_id: int, db: Session = Depends(get_sync_session)):
    """Get a node by ID."""
    node = get_node(db=db, node_id=node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


# Template endpoints
@router.post("/templates/", response_model=TemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template_endpoint(
    template: TemplateSchema, 
    db: Session = Depends(get_sync_session)
):
    """Create a new template."""
    return create_template(db=db, template=template)


@router.get("/templates/", response_model=List[TemplateSchema])
def get_all_templates_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_sync_session)
):
    """Get all templates with pagination."""
    return get_all_templates(db=db, skip=skip, limit=limit)


@router.get("/templates/{template_id}", response_model=TemplateSchema)
def get_template_endpoint(template_id: int, db: Session = Depends(get_sync_session)):
    """Get a template by ID."""
    template = get_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
