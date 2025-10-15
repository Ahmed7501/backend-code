"""
Celery configuration settings.
"""

import os
from typing import Optional


class CelerySettings:
    """Celery configuration settings."""
    
    # Broker settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Task settings
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_RESULT_SERIALIZER: str = "json"
    
    # Timezone settings
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    
    # Task execution settings
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800"))  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "1500"))  # 25 minutes
    
    # Worker settings
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_WORKER_DISABLE_RATE_LIMITS: bool = False
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
    
    # Retry settings
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = int(os.getenv("CELERY_TASK_DEFAULT_RETRY_DELAY", "60"))  # 1 minute
    CELERY_TASK_MAX_RETRIES: int = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))
    
    # Result settings
    CELERY_RESULT_EXPIRES: int = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))  # 1 hour
    CELERY_RESULT_PERSISTENT: bool = True
    
    # Flow execution settings
    FLOW_EXECUTION_TIMEOUT: int = int(os.getenv("FLOW_EXECUTION_TIMEOUT", "1800"))  # 30 minutes
    FLOW_CLEANUP_INTERVAL: int = int(os.getenv("FLOW_CLEANUP_INTERVAL", "3600"))  # 1 hour


celery_settings = CelerySettings()
