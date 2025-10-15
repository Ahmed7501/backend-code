"""
Celery tasks for analytics aggregation and processing.
"""

import logging
from datetime import datetime, timedelta, date
from celery import current_task
from sqlalchemy.orm import Session

from ..flow_engine.celery_app import celery_app
from ..shared.database import get_sync_session
from .crud import aggregate_daily_stats, aggregate_hourly_stats, cleanup_old_stats

logger = logging.getLogger(__name__)


@celery_app.task(name="src.analytics.tasks.aggregate_daily_stats")
def aggregate_daily_stats_task(date_str: str = None):
    """
    Aggregate statistics for a specific date.
    Runs daily at midnight to aggregate previous day's data.
    """
    try:
        # Determine target date
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            # Default to previous day
            target_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        logger.info(f"Starting daily stats aggregation for {target_date}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Aggregate stats for all bots
        aggregated_stats = aggregate_daily_stats(db, target_date)
        
        bot_count = len(set(stat.bot_id for stat in aggregated_stats))
        total_messages = sum(stat.total_messages for stat in aggregated_stats)
        
        logger.info(f"Successfully aggregated daily stats for {bot_count} bots on {target_date}: {total_messages} total messages")
        
        return {
            "success": True,
            "date": target_date.isoformat(),
            "bots_processed": bot_count,
            "total_messages": total_messages,
            "stats_created": len(aggregated_stats)
        }
    
    except Exception as e:
        logger.error(f"Failed to aggregate daily stats for {date_str}: {str(e)}")
        
        # Retry the task if it's a temporary error
        if current_task.request.retries < current_task.max_retries:
            logger.info(f"Retrying aggregate_daily_stats task (attempt {current_task.request.retries + 1})")
            raise current_task.retry(countdown=60 * (current_task.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.analytics.tasks.aggregate_hourly_stats")
def aggregate_hourly_stats_task(hour_str: str = None):
    """
    Aggregate hourly statistics for real-time insights.
    Runs every hour.
    """
    try:
        # Determine target hour
        if hour_str:
            target_hour = datetime.fromisoformat(hour_str)
        else:
            # Default to previous hour
            target_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        
        logger.info(f"Starting hourly stats aggregation for {target_hour}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Aggregate stats for all bots
        aggregated_stats = aggregate_hourly_stats(db, target_hour)
        
        bot_count = len(set(stat.bot_id for stat in aggregated_stats))
        total_messages = sum(stat.total_messages for stat in aggregated_stats)
        
        logger.info(f"Successfully aggregated hourly stats for {bot_count} bots at {target_hour}: {total_messages} messages")
        
        return {
            "success": True,
            "hour": target_hour.isoformat(),
            "bots_processed": bot_count,
            "total_messages": total_messages,
            "stats_created": len(aggregated_stats)
        }
    
    except Exception as e:
        logger.error(f"Failed to aggregate hourly stats for {hour_str}: {str(e)}")
        
        # Retry the task if it's a temporary error
        if current_task.request.retries < current_task.max_retries:
            logger.info(f"Retrying aggregate_hourly_stats task (attempt {current_task.request.retries + 1})")
            raise current_task.retry(countdown=60 * (current_task.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.analytics.tasks.cleanup_old_stats")
def cleanup_old_stats_task():
    """
    Clean up hourly stats older than 7 days.
    Keep daily stats for longer period (90 days).
    """
    try:
        logger.info("Starting cleanup of old analytics statistics")
        
        # Get database session
        db = next(get_sync_session())
        
        # Clean up old stats
        cleanup_result = cleanup_old_stats(db, days_to_keep_hourly=7, days_to_keep_daily=90)
        
        logger.info(f"Successfully cleaned up {cleanup_result['hourly_deleted']} hourly stats and {cleanup_result['daily_deleted']} daily stats")
        
        return {
            "success": True,
            "hourly_deleted": cleanup_result["hourly_deleted"],
            "daily_deleted": cleanup_result["daily_deleted"]
        }
    
    except Exception as e:
        logger.error(f"Failed to cleanup old stats: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.analytics.tasks.aggregate_stats_for_bot")
def aggregate_stats_for_bot_task(bot_id: int, date_str: str = None):
    """
    Aggregate statistics for a specific bot and date.
    Useful for manual aggregation or backfilling data.
    """
    try:
        # Determine target date
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            # Default to previous day
            target_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        logger.info(f"Starting stats aggregation for bot {bot_id} on {target_date}")
        
        # Get database session
        db = next(get_sync_session())
        
        # Aggregate stats for specific bot
        aggregated_stats = aggregate_daily_stats(db, target_date, bot_id)
        
        if aggregated_stats:
            stats = aggregated_stats[0]
            logger.info(f"Successfully aggregated stats for bot {bot_id} on {target_date}: {stats.total_messages} messages")
            
            return {
                "success": True,
                "bot_id": bot_id,
                "date": target_date.isoformat(),
                "total_messages": stats.total_messages,
                "active_contacts": stats.active_contacts,
                "delivery_rate": round((stats.delivered_count / stats.sent_count * 100) if stats.sent_count > 0 else 0, 2)
            }
        else:
            logger.warning(f"No stats aggregated for bot {bot_id} on {target_date}")
            return {
                "success": True,
                "bot_id": bot_id,
                "date": target_date.isoformat(),
                "message": "No data found for aggregation"
            }
    
    except Exception as e:
        logger.error(f"Failed to aggregate stats for bot {bot_id} on {date_str}: {str(e)}")
        
        # Retry the task if it's a temporary error
        if current_task.request.retries < current_task.max_retries:
            logger.info(f"Retrying aggregate_stats_for_bot task (attempt {current_task.request.retries + 1})")
            raise current_task.retry(countdown=60 * (current_task.request.retries + 1))
        
        return {"success": False, "error": str(e)}


@celery_app.task(name="src.analytics.tasks.backfill_analytics")
def backfill_analytics_task(start_date_str: str, end_date_str: str, bot_id: int = None):
    """
    Backfill analytics data for a date range.
    Useful for historical data processing.
    """
    try:
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()
        
        logger.info(f"Starting analytics backfill from {start_date} to {end_date}")
        
        # Get database session
        db = next(get_sync_session())
        
        aggregated_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            try:
                aggregated_stats = aggregate_daily_stats(db, current_date, bot_id)
                aggregated_count += len(aggregated_stats)
                logger.info(f"Backfilled stats for {current_date}: {len(aggregated_stats)} records")
            except Exception as e:
                logger.error(f"Failed to backfill stats for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        logger.info(f"Successfully backfilled analytics for {aggregated_count} records")
        
        return {
            "success": True,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "bot_id": bot_id,
            "records_created": aggregated_count
        }
    
    except Exception as e:
        logger.error(f"Failed to backfill analytics: {str(e)}")
        return {"success": False, "error": str(e)}
