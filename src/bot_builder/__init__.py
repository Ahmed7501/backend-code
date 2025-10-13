"""
Bot Builder module for WhatsApp bot management.
"""

from .router import router
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

from ..shared.models.bot_builder import Bot, BotFlow, BotNode, Template
from ..shared.schemas.bot_builder import BotSchema, FlowSchema, NodeSchema, TemplateSchema

__all__ = [
    "router",
    "create_bot",
    "get_bot", 
    "get_all_bots",
    "update_bot",
    "delete_bot",
    "create_flow",
    "get_flow",
    "get_all_flows",
    "create_node",
    "get_node",
    "get_all_nodes",
    "create_template",
    "get_template",
    "get_all_templates",
    "Bot",
    "BotFlow",
    "BotNode",
    "Template",
    "BotSchema",
    "FlowSchema",
    "NodeSchema",
    "TemplateSchema"
]
