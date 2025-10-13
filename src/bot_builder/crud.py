"""
CRUD operations for bot builder functionality.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..shared.models.bot_builder import Bot, BotFlow, BotNode, Template
from ..shared.schemas.bot_builder import BotSchema, FlowSchema, NodeSchema, TemplateSchema


# Bot CRUD operations
def create_bot(db: Session, bot: BotSchema) -> Bot:
    """Create a new bot."""
    new_bot = Bot(name=bot.name, description=bot.description)
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot


def get_bot(db: Session, bot_id: int) -> Optional[Bot]:
    """Get a bot by ID."""
    return db.query(Bot).filter(Bot.id == bot_id).first()


def get_all_bots(db: Session, skip: int = 0, limit: int = 100) -> List[Bot]:
    """Get all bots with pagination."""
    return db.query(Bot).offset(skip).limit(limit).all()


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
    """Get a flow by ID."""
    return db.query(BotFlow).filter(BotFlow.id == flow_id).first()


def get_all_flows(db: Session, skip: int = 0, limit: int = 100) -> List[BotFlow]:
    """Get all flows with pagination."""
    return db.query(BotFlow).offset(skip).limit(limit).all()


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


def get_all_nodes(db: Session, skip: int = 0, limit: int = 100) -> List[BotNode]:
    """Get all nodes with pagination."""
    return db.query(BotNode).offset(skip).limit(limit).all()


# Template CRUD operations
def create_template(db: Session, template: TemplateSchema) -> Template:
    """Create a new template."""
    new_template = Template(
        name=template.name, 
        structure=[n.dict() for n in template.structure]
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template


def get_template(db: Session, template_id: int) -> Optional[Template]:
    """Get a template by ID."""
    return db.query(Template).filter(Template.id == template_id).first()


def get_all_templates(db: Session, skip: int = 0, limit: int = 100) -> List[Template]:
    """Get all templates with pagination."""
    return db.query(Template).offset(skip).limit(limit).all()
