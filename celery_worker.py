#!/usr/bin/env python3
"""
Celery worker script for ChatBoost Flow Engine.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables if not already set
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

if __name__ == "__main__":
    from src.flow_engine.celery_app import celery_app
    
    # Start Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=flow_execution,webhook_actions,maintenance",
        "--hostname=flow-engine@%h"
    ])
