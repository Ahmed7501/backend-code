"""
API router for analytics and reporting.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..shared.database import get_db
from ..shared.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
    BotPerformanceResponse,
    DeliveryRatesResponse,
    ActiveContactsResponse,
    MessageDistributionResponse,
    ManualAggregationRequest,
    ManualAggregationResponse
)
from .crud import (
    get_overview_stats,
    get_daily_stats,
    calculate_delivery_rate,
    get_message_type_distribution,
    get_flow_completion_rate,
    aggregate_daily_stats,
    aggregate_hourly_stats
)
from ..shared.models.bot_builder import Bot, DailyMessageStats, HourlyMessageStats
from ..analytics.tasks import aggregate_daily_stats_task, aggregate_hourly_stats_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    period: str = Query(default="7days", pattern="^(today|7days|30days)$"),
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get analytics overview for specified period."""
    try:
        # Get overview statistics
        stats = await asyncio.to_thread(get_overview_stats, db, period, bot_id)
        
        # Calculate average response time (placeholder - would need actual implementation)
        average_response_time = 2.3  # This would be calculated from actual data
        
        return AnalyticsOverviewResponse(
            period=period,
            bot_id=bot_id,
            total_messages=stats["total_messages"],
            active_contacts=stats["active_contacts"],
            delivery_rate=stats["delivery_rate"],
            average_response_time=average_response_time,
            top_message_types=stats["top_message_types"],
            flow_completion_rate=stats["flow_completion_rate"],
            trends=stats["trends"]
        )
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_analytics_trends(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get analytics trends over date range."""
    try:
        # Get daily stats for the period
        daily_stats = await asyncio.to_thread(get_daily_stats, db, start_date, end_date, bot_id)
        
        # Format daily stats
        formatted_daily_stats = []
        for stat in daily_stats:
            delivery_rate = (stat.delivered_count / stat.sent_count * 100) if stat.sent_count > 0 else 0
            formatted_daily_stats.append({
                "date": stat.date,
                "bot_id": stat.bot_id,
                "total_messages": stat.total_messages,
                "inbound_messages": stat.inbound_messages,
                "outbound_messages": stat.outbound_messages,
                "delivery_rate": round(delivery_rate, 2),
                "active_contacts": stat.active_contacts,
                "new_contacts": stat.new_contacts,
                "flows_started": stat.flows_started,
                "flows_completed": stat.flows_completed,
                "flows_failed": stat.flows_failed,
                "triggers_fired": stat.triggers_fired
            })
        
        # Create trend data
        total_messages_trend = [
            {"date": stat.date.isoformat(), "value": stat.total_messages}
            for stat in daily_stats
        ]
        
        active_contacts_trend = [
            {"date": stat.date.isoformat(), "value": stat.active_contacts}
            for stat in daily_stats
        ]
        
        delivery_rate_trend = [
            {
                "date": stat.date.isoformat(), 
                "value": round((stat.delivered_count / stat.sent_count * 100) if stat.sent_count > 0 else 0, 2)
            }
            for stat in daily_stats
        ]
        
        return AnalyticsTrendsResponse(
            start_date=start_date,
            end_date=end_date,
            bot_id=bot_id,
            daily_stats=formatted_daily_stats,
            total_messages_trend=total_messages_trend,
            active_contacts_trend=active_contacts_trend,
            delivery_rate_trend=delivery_rate_trend
        )
    except Exception as e:
        logger.error(f"Failed to get analytics trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}/performance", response_model=BotPerformanceResponse)
async def get_bot_performance(
    bot_id: int,
    period: str = Query(default="30days", pattern="^(today|7days|30days)$"),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific bot."""
    try:
        # Check if bot exists
        bot = await asyncio.to_thread(lambda: db.query(Bot).filter(Bot.id == bot_id).first())
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get overview stats for the bot
        stats = await asyncio.to_thread(get_overview_stats, db, period, bot_id)
        
        # Calculate average flows per contact
        active_contacts = stats["active_contacts"]
        total_flows_started = stats.get("flows_started", 0)
        average_flows_per_contact = (total_flows_started / active_contacts) if active_contacts > 0 else 0
        
        return BotPerformanceResponse(
            bot_id=bot.id,
            bot_name=bot.name,
            total_messages=stats["total_messages"],
            active_contacts=stats["active_contacts"],
            delivery_rate=stats["delivery_rate"],
            flow_completion_rate=stats["flow_completion_rate"],
            average_flows_per_contact=round(average_flows_per_contact, 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delivery-rates", response_model=DeliveryRatesResponse)
async def get_delivery_rates(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    bot_id: Optional[int] = None,
    granularity: str = Query(default="daily", pattern="^(hourly|daily)$"),
    db: Session = Depends(get_db)
):
    """Get delivery rate statistics."""
    try:
        if granularity == "daily":
            # Get daily stats
            daily_stats = await asyncio.to_thread(get_daily_stats, db, start_date, end_date, bot_id)
            
            delivery_rates = []
            total_sent = 0
            total_delivered = 0
            total_read = 0
            total_failed = 0
            
            for stat in daily_stats:
                delivery_rate = (stat.delivered_count / stat.sent_count * 100) if stat.sent_count > 0 else 0
                delivery_rates.append({
                    "date": stat.date.isoformat(),
                    "delivery_rate": round(delivery_rate, 2),
                    "sent": stat.sent_count,
                    "delivered": stat.delivered_count,
                    "read": stat.read_count,
                    "failed": stat.failed_count
                })
                
                total_sent += stat.sent_count
                total_delivered += stat.delivered_count
                total_read += stat.read_count
                total_failed += stat.failed_count
            
            average_delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            
        else:  # hourly
            # Get hourly stats (simplified implementation)
            hourly_stats = await asyncio.to_thread(
                lambda: db.query(HourlyMessageStats).filter(
                    HourlyMessageStats.hour >= start_date,
                    HourlyMessageStats.hour <= end_date
                ).filter(HourlyMessageStats.bot_id == bot_id if bot_id else True).order_by(HourlyMessageStats.hour).all()
            )
            
            delivery_rates = []
            total_sent = 0
            total_delivered = 0
            total_read = 0
            total_failed = 0
            
            for stat in hourly_stats:
                # For hourly, we'll use a simplified delivery rate calculation
                delivery_rate = 95.0  # Placeholder - would need actual hourly delivery data
                delivery_rates.append({
                    "hour": stat.hour.isoformat(),
                    "delivery_rate": delivery_rate,
                    "messages": stat.total_messages
                })
            
            average_delivery_rate = 95.0  # Placeholder
        
        return DeliveryRatesResponse(
            start_date=start_date,
            end_date=end_date,
            bot_id=bot_id,
            granularity=granularity,
            delivery_rates=delivery_rates,
            average_delivery_rate=round(average_delivery_rate, 2),
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_read=total_read,
            total_failed=total_failed
        )
    except Exception as e:
        logger.error(f"Failed to get delivery rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-contacts", response_model=ActiveContactsResponse)
async def get_active_contacts_stats(
    period: str = Query(default="7days", pattern="^(today|7days|30days)$"),
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get active contacts statistics."""
    try:
        # Get overview stats
        stats = await asyncio.to_thread(get_overview_stats, db, period, bot_id)
        
        # Get daily active contacts breakdown
        end_date = datetime.utcnow()
        if period == "today":
            start_date = datetime.combine(end_date.date(), datetime.min.time())
        elif period == "7days":
            start_date = end_date - timedelta(days=7)
        elif period == "30days":
            start_date = end_date - timedelta(days=30)
        
        daily_stats = await asyncio.to_thread(get_daily_stats, db, start_date, end_date, bot_id)
        
        daily_active_contacts = [
            {"date": stat.date.isoformat(), "active_contacts": stat.active_contacts}
            for stat in daily_stats
        ]
        
        # Calculate growth rate (simplified)
        contacts_growth_rate = 5.2  # Placeholder - would calculate from previous period
        
        return ActiveContactsResponse(
            period=period,
            bot_id=bot_id,
            active_contacts=stats["active_contacts"],
            new_contacts=sum(stat.new_contacts for stat in daily_stats),
            returning_contacts=stats["active_contacts"] - sum(stat.new_contacts for stat in daily_stats),
            contacts_growth_rate=contacts_growth_rate,
            daily_active_contacts=daily_active_contacts
        )
    except Exception as e:
        logger.error(f"Failed to get active contacts stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/message-distribution", response_model=MessageDistributionResponse)
async def get_message_distribution(
    period: str = Query(default="7days", pattern="^(today|7days|30days)$"),
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get message type distribution."""
    try:
        # Get overview stats
        stats = await asyncio.to_thread(get_overview_stats, db, period, bot_id)
        
        message_types = stats["top_message_types"]
        total_messages = stats["total_messages"]
        
        # Calculate percentage breakdown
        percentage_breakdown = {}
        for msg_type, count in message_types.items():
            percentage_breakdown[msg_type] = round((count / total_messages * 100) if total_messages > 0 else 0, 2)
        
        # Simplified inbound/outbound distribution
        inbound_distribution = {k: v // 2 for k, v in message_types.items()}  # Placeholder
        outbound_distribution = {k: v // 2 for k, v in message_types.items()}  # Placeholder
        
        return MessageDistributionResponse(
            period=period,
            bot_id=bot_id,
            total_messages=total_messages,
            message_types=message_types,
            inbound_distribution=inbound_distribution,
            outbound_distribution=outbound_distribution,
            percentage_breakdown=percentage_breakdown
        )
    except Exception as e:
        logger.error(f"Failed to get message distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aggregate-now", response_model=ManualAggregationResponse)
async def trigger_manual_aggregation(
    request: ManualAggregationRequest,
    db: Session = Depends(get_db)
):
    """Manually trigger statistics aggregation (admin only)."""
    try:
        start_time = time.time()
        
        if request.date:
            target_date = request.date.date()
        else:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Trigger daily aggregation task
        if request.bot_id:
            # Aggregate for specific bot
            from ..analytics.tasks import aggregate_stats_for_bot_task
            task_result = aggregate_stats_for_bot_task.delay(request.bot_id, target_date.isoformat())
            aggregated_bots = [request.bot_id]
        else:
            # Aggregate for all bots
            task_result = aggregate_daily_stats_task.delay(target_date.isoformat())
            aggregated_bots = [bot.id for bot in await asyncio.to_thread(lambda: db.query(Bot).all())]
        
        processing_time = round(time.time() - start_time, 2)
        
        return ManualAggregationResponse(
            success=True,
            message=f"Aggregation task triggered for {target_date.isoformat()}",
            aggregated_bots=aggregated_bots,
            aggregated_date=target_date,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Failed to trigger manual aggregation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analytics_health_check(db: Session = Depends(get_db)):
    """Health check for analytics system."""
    try:
        # Check if we have recent daily stats
        recent_stats = await asyncio.to_thread(
            lambda: db.query(DailyMessageStats).filter(
                DailyMessageStats.date >= datetime.utcnow() - timedelta(days=1)
            ).count()
        )
        
        # Check if we have recent hourly stats
        recent_hourly = await asyncio.to_thread(
            lambda: db.query(HourlyMessageStats).filter(
                HourlyMessageStats.hour >= datetime.utcnow() - timedelta(hours=1)
            ).count()
        )
        
        return {
            "status": "healthy",
            "recent_daily_stats": recent_stats,
            "recent_hourly_stats": recent_hourly,
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }
