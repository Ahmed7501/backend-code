
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # WhatsApp integration fields
    whatsapp_access_token = Column(String, nullable=True)
    whatsapp_phone_number_id = Column(String, nullable=True)
    whatsapp_business_account_id = Column(String, nullable=True)
    is_whatsapp_enabled = Column(Boolean, default=False)

    flows = relationship("BotFlow", back_populates="bot")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="bot")


class BotFlow(Base):
    __tablename__ = "bot_flows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    structure = Column(JSON)  # JSON flow data

    bot = relationship("Bot", back_populates="flows")
    nodes = relationship("BotNode", back_populates="flow")


class BotNode(Base):
    __tablename__ = "bot_nodes"
    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("bot_flows.id"))
    node_type = Column(String)
    content = Column(JSON)

    flow = relationship("BotFlow", back_populates="nodes")


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    structure = Column(JSON)


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    whatsapp_message_id = Column(String, unique=True, index=True)
    direction = Column(String)  # 'inbound' or 'outbound'
    message_type = Column(String)  # 'text', 'template', 'media', 'interactive'
    content = Column(JSON)
    recipient_phone = Column(String)
    sender_phone = Column(String)
    status = Column(String)  # 'sent', 'delivered', 'read', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bot = relationship("Bot", back_populates="whatsapp_messages")


class WhatsAppWebhookEvent(Base):
    __tablename__ = "whatsapp_webhook_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)  # 'message', 'status', 'error'
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
