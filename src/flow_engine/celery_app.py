"""
Celery configuration for flow engine tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab
from config.settings import settings

# Create Celery instance
celery_app = Celery(
    "chatboost_flow_engine",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "src.flow_engine.tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    result_expires=3600,  # 1 hour
    result_persistent=True,
)

# Task routes
celery_app.conf.task_routes = {
    "src.flow_engine.tasks.resume_flow_after_wait": {"queue": "flow_execution"},
    "src.flow_engine.tasks.execute_webhook_action": {"queue": "webhook_actions"},
    "src.flow_engine.tasks.cleanup_old_executions": {"queue": "maintenance"},
}

# Periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-executions": {
        "task": "src.flow_engine.tasks.cleanup_old_executions",
        "schedule": 3600.0,  # Run every hour
    },
    "check-pending-triggers": {
        "task": "src.triggers.tasks.check_pending_triggers",
        "schedule": 60.0,  # Check every minute
    },
    "update-trigger-schedules": {
        "task": "src.triggers.tasks.update_trigger_schedules",
        "schedule": 3600.0,  # Update every hour
    },
    "aggregate-daily-stats": {
        "task": "src.analytics.tasks.aggregate_daily_stats",
        "schedule": crontab(hour=0, minute=5),  # Run at 00:05 daily
    },
    "aggregate-hourly-stats": {
        "task": "src.analytics.tasks.aggregate_hourly_stats",
        "schedule": 3600.0,  # Run every hour
    },
    "cleanup-old-analytics": {
        "task": "src.analytics.tasks.cleanup_old_stats",
        "schedule": crontab(hour=2, minute=0),  # Run at 02:00 daily
    },
    "cleanup-old-notifications": {
        "task": "src.notifications.tasks.cleanup_old_notifications",
        "schedule": crontab(hour=3, minute=0),  # Run at 03:00 daily
    },
    "cleanup-stale-websocket-connections": {
        "task": "src.notifications.tasks.cleanup_stale_websocket_connections",
        "schedule": 300.0,  # Run every 5 minutes
    },
    "send-notification-reminders": {
        "task": "src.notifications.tasks.send_notification_reminders",
        "schedule": crontab(hour=9, minute=0),  # Run at 09:00 daily
    },
    "notification-analytics": {
        "task": "src.notifications.tasks.notification_analytics",
        "schedule": crontab(hour=4, minute=0),  # Run at 04:00 daily
    },
}
