"""
Analytics module for ChatBoost backend.
"""

from .crud import (
    aggregate_daily_stats,
    get_daily_stats,
    get_overview_stats,
    calculate_delivery_rate,
    get_active_contacts_count,
    get_message_type_distribution,
    get_flow_completion_rate,
    calculate_trends,
    aggregate_hourly_stats,
    cleanup_old_stats
)

from .tasks import (
    aggregate_daily_stats_task,
    aggregate_hourly_stats_task,
    cleanup_old_stats_task,
    aggregate_stats_for_bot_task,
    backfill_analytics_task
)

__all__ = [
    # CRUD operations
    "aggregate_daily_stats",
    "get_daily_stats", 
    "get_overview_stats",
    "calculate_delivery_rate",
    "get_active_contacts_count",
    "get_message_type_distribution",
    "get_flow_completion_rate",
    "calculate_trends",
    "aggregate_hourly_stats",
    "cleanup_old_stats",
    
    # Celery tasks
    "aggregate_daily_stats_task",
    "aggregate_hourly_stats_task", 
    "cleanup_old_stats_task",
    "aggregate_stats_for_bot_task",
    "backfill_analytics_task"
]
