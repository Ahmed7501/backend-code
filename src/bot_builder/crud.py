"""
CRUD operations for bot builder functionality.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..flow_engine.flow_normalizer import FlowNormalizer
from ..shared.models.bot_builder import Bot, BotFlow, BotNode, Template
from ..shared.schemas.bot_builder import BotSchema, FlowSchema, NodeSchema, TemplateCreate, TemplateResponse


# Bot CRUD operations
def create_bot(db: Session, bot: BotSchema, created_by_id: int, organization_id: Optional[int] = None) -> Bot:
    """Create a new bot with explicit ownership tracking."""
    # Extract fields from the schema
    bot_data = bot.dict()
    
    # Create new bot with explicit ownership
    new_bot = Bot(
        name=bot_data["name"],
        description=bot_data.get("description"),
        whatsapp_access_token=bot_data.get("whatsapp_access_token"),
        whatsapp_phone_number_id=bot_data.get("whatsapp_phone_number_id"),
        whatsapp_business_account_id=bot_data.get("whatsapp_business_account_id"),
        is_whatsapp_enabled=bot_data.get("is_whatsapp_enabled", False),
        created_by_id=created_by_id,  # Explicitly set from parameter
        organization_id=organization_id  # Explicitly set from parameter
    )
    
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot


def get_bot(db: Session, bot_id: int) -> Optional[Bot]:
    """Get a bot by ID."""
    return db.query(Bot).filter(Bot.id == bot_id).first()


def get_all_bots(db: Session, skip: int = 0, limit: int = 100, created_by_id: int = None) -> List[Bot]:
    """Get all bots with pagination."""
    query = db.query(Bot)
    if created_by_id:
        query = query.filter(Bot.created_by_id == created_by_id)
    return query.offset(skip).limit(limit).all()


def update_bot(db: Session, bot_id: int, bot_update: dict) -> Optional[Bot]:
    """Update a bot."""
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not db_bot:
        return None
    
    for field, value in bot_update.items():
        if hasattr(db_bot, field):
            setattr(db_bot, field, value)
    
    db.commit()
    db.refresh(db_bot)
    return db_bot


def delete_bot(db: Session, bot_id: int) -> bool:
    """Delete a bot."""
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not db_bot:
        return False
    
    db.delete(db_bot)
    db.commit()
    return True


# Flow CRUD operations
def create_flow(db: Session, flow: FlowSchema) -> BotFlow:
    """Create a new flow."""
    new_flow = BotFlow(
        name=flow.name, 
        bot_id=flow.bot_id, 
        structure=[n.dict() for n in flow.structure]
    )
    db.add(new_flow)
    db.commit()
    db.refresh(new_flow)
    return new_flow


def get_flow(db: Session, flow_id: int) -> Optional[BotFlow]:
    """Get a flow by ID with normalized structure."""
    flow = db.query(BotFlow).filter(BotFlow.id == flow_id).first()
    if flow and flow.structure:
        # Normalize structure for backward compatibility
        flow.structure = FlowNormalizer.normalize_flow_structure(flow.structure)
    return flow


def get_all_flows(db: Session, skip: int = 0, limit: int = 100, created_by_id: int = None) -> List[BotFlow]:
    """Get all flows with normalized structures."""
    query = db.query(BotFlow)
    if created_by_id:
        # Filter flows by bot ownership
        query = query.join(Bot).filter(Bot.created_by_id == created_by_id)
    
    flows = query.offset(skip).limit(limit).all()
    
    # Normalize all flows
    for flow in flows:
        if flow.structure:
            flow.structure = FlowNormalizer.normalize_flow_structure(flow.structure)
    
    return flows


# Node CRUD operations
def create_node(db: Session, node: NodeSchema, flow_id: int) -> BotNode:
    """Create a new node."""
    new_node = BotNode(
        flow_id=flow_id, 
        node_type=node.node_type, 
        content=node.content
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node


def get_node(db: Session, node_id: int) -> Optional[BotNode]:
    """Get a node by ID."""
    return db.query(BotNode).filter(BotNode.id == node_id).first()


def get_all_nodes(db: Session, skip: int = 0, limit: int = 100, created_by_id: Optional[int] = None) -> List[BotNode]:
    """Get all nodes with pagination."""
    query = db.query(BotNode)
    if created_by_id:
        # Filter nodes by flow → bot ownership
        query = query.join(BotFlow).join(Bot).filter(Bot.created_by_id == created_by_id)
    return query.offset(skip).limit(limit).all()


# Template CRUD operations
def create_template(db: Session, template: TemplateCreate, created_by_id: int) -> Template:
    """Create a new template with automatic ownership assignment."""
    new_template = Template(
        name=template.name,
        structure=[n.dict() for n in template.structure],
        created_by_id=created_by_id
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template


def get_template(db: Session, template_id: int) -> Optional[Template]:
    """Get a template by ID."""
    return db.query(Template).filter(Template.id == template_id).first()


def get_all_templates(db: Session, skip: int = 0, limit: int = 100, created_by_id: Optional[int] = None) -> List[Template]:
    """Get all templates with pagination."""
    query = db.query(Template)
    if created_by_id:
        # Filter by ownership or show global templates (created_by_id is None)
        query = query.filter((Template.created_by_id == created_by_id) | (Template.created_by_id.is_(None)))
    return query.offset(skip).limit(limit).all()
