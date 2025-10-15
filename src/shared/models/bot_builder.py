
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # WhatsApp integration fields
    whatsapp_access_token = Column(String, nullable=True)
    whatsapp_phone_number_id = Column(String, nullable=True)
    whatsapp_business_account_id = Column(String, nullable=True)
    is_whatsapp_enabled = Column(Boolean, default=False)

    organization = relationship("Organization", back_populates="bots")
    created_by = relationship("User")
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


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    meta_data = Column(JSON, default={})  # Custom fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    executions = relationship("FlowExecution", back_populates="contact")
    attributes = relationship("ContactAttribute", back_populates="contact", cascade="all, delete-orphan")


class FlowExecution(Base):
    __tablename__ = "flow_executions"
    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("bot_flows.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    bot_id = Column(Integer, ForeignKey("bots.id"))
    current_node_index = Column(Integer, default=0)
    state = Column(JSON, default={})  # Variables and context
    status = Column(String)  # 'running', 'waiting', 'completed', 'failed'
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_executed_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("Contact", back_populates="executions")
    flow = relationship("BotFlow")
    bot = relationship("Bot")
    logs = relationship("FlowExecutionLog", back_populates="execution")


class FlowExecutionLog(Base):
    __tablename__ = "flow_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("flow_executions.id"))
    node_index = Column(Integer)
    node_type = Column(String)
    action = Column(String)  # 'executed', 'skipped', 'failed'
    result = Column(JSON)
    error = Column(String, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("FlowExecution", back_populates="logs")


class Trigger(Base):
    __tablename__ = "triggers"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    flow_id = Column(Integer, ForeignKey("bot_flows.id"))
    name = Column(String)
    trigger_type = Column(String)  # 'keyword', 'event', 'schedule'
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority triggers checked first
    
    # Keyword trigger fields
    keywords = Column(JSON)  # List of keywords/phrases
    match_type = Column(String)  # 'exact', 'contains', 'starts_with', 'ends_with', 'regex'
    case_sensitive = Column(Boolean, default=False)
    
    # Event trigger fields
    event_type = Column(String)  # 'new_contact', 'message_received', 'opt_in', 'opt_out'
    event_conditions = Column(JSON)  # Additional event conditions
    
    # Schedule trigger fields
    schedule_type = Column(String)  # 'once', 'daily', 'weekly', 'monthly', 'cron'
    schedule_time = Column(String)  # Time/cron expression
    schedule_timezone = Column(String, default='UTC')
    last_triggered_at = Column(DateTime, nullable=True)
    next_trigger_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    bot = relationship("Bot")
    flow = relationship("BotFlow")
    logs = relationship("TriggerLog", back_populates="trigger")


class TriggerLog(Base):
    __tablename__ = "trigger_logs"
    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    execution_id = Column(Integer, ForeignKey("flow_executions.id"), nullable=True)
    matched_value = Column(String)  # What triggered it
    triggered_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error = Column(String, nullable=True)
    
    trigger = relationship("Trigger", back_populates="logs")
    contact = relationship("Contact")
    execution = relationship("FlowExecution")


class ContactAttribute(Base):
    __tablename__ = "contact_attributes"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    key = Column(String, index=True)
    value = Column(String)
    value_type = Column(String)  # 'string', 'number', 'boolean', 'json'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    contact = relationship("Contact", back_populates="attributes")
    
    # Unique constraint for contact_id + key
    __table_args__ = (UniqueConstraint('contact_id', 'key', name='_contact_key_uc'),)


class DailyMessageStats(Base):
    __tablename__ = "daily_message_stats"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    date = Column(DateTime, index=True)  # Date for the aggregation
    
    # Message counts
    total_messages = Column(Integer, default=0)
    inbound_messages = Column(Integer, default=0)
    outbound_messages = Column(Integer, default=0)
    
    # Message types
    text_messages = Column(Integer, default=0)
    template_messages = Column(Integer, default=0)
    media_messages = Column(Integer, default=0)
    interactive_messages = Column(Integer, default=0)
    
    # Delivery stats
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Contact stats
    active_contacts = Column(Integer, default=0)  # Unique contacts who sent/received messages
    new_contacts = Column(Integer, default=0)  # Contacts created on this day
    
    # Flow stats
    flows_started = Column(Integer, default=0)
    flows_completed = Column(Integer, default=0)
    flows_failed = Column(Integer, default=0)
    
    # Trigger stats
    triggers_fired = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    bot = relationship("Bot")
    
    # Unique constraint for bot_id + date
    __table_args__ = (UniqueConstraint('bot_id', 'date', name='_bot_date_uc'),)


class HourlyMessageStats(Base):
    __tablename__ = "hourly_message_stats"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    hour = Column(DateTime, index=True)  # Hour timestamp
    
    total_messages = Column(Integer, default=0)
    inbound_messages = Column(Integer, default=0)
    outbound_messages = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bot = relationship("Bot")
    
    __table_args__ = (UniqueConstraint('bot_id', 'hour', name='_bot_hour_uc'),)


class Notification(Base):
    """Notification model for real-time notifications."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    type = Column(String)  # 'message_status', 'flow_event', 'system', 'mention'
    title = Column(String)
    message = Column(String)
    data = Column(JSON)  # Additional notification data
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="normal")  # 'low', 'normal', 'high', 'urgent'
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    user = relationship("User")
    organization = relationship("Organization")


class NotificationPreference(Base):
    """Notification preferences model for user settings."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    message_status_enabled = Column(Boolean, default=True)
    flow_events_enabled = Column(Boolean, default=True)
    system_notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    user = relationship("User")
