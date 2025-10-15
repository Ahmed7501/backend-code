"""
Caching layer for analytics data using Redis.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from config.settings import settings

logger = logging.getLogger(__name__)

# Redis connection
redis_client = None

def get_redis_client():
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established for analytics caching")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None
    return redis_client


def cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from prefix and parameters."""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)


def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    """Get cached data from Redis."""
    try:
        client = get_redis_client()
        if not client:
            return None
        
        cached_data = client.get(key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Failed to get cached data for key {key}: {e}")
    return None


def set_cached_data(key: str, data: Dict[str, Any], ttl: int = 300) -> bool:
    """Set cached data in Redis with TTL."""
    try:
        client = get_redis_client()
        if not client:
            return False
        
        client.setex(key, ttl, json.dumps(data, default=str))
        return True
    except Exception as e:
        logger.error(f"Failed to set cached data for key {key}: {e}")
        return False


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache entries matching pattern."""
    try:
        client = get_redis_client()
        if not client:
            return 0
        
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
    return 0


def cache_overview_stats(period: str, bot_id: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache overview statistics."""
    key = cache_key("analytics:overview", period=period, bot_id=bot_id)
    return set_cached_data(key, data, ttl=300)  # 5 minutes


def get_cached_overview_stats(period: str, bot_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Get cached overview statistics."""
    key = cache_key("analytics:overview", period=period, bot_id=bot_id)
    return get_cached_data(key)


def cache_trends_data(start_date: str, end_date: str, bot_id: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache trends data."""
    key = cache_key("analytics:trends", start_date=start_date, end_date=end_date, bot_id=bot_id)
    return set_cached_data(key, data, ttl=900)  # 15 minutes


def get_cached_trends_data(start_date: str, end_date: str, bot_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Get cached trends data."""
    key = cache_key("analytics:trends", start_date=start_date, end_date=end_date, bot_id=bot_id)
    return get_cached_data(key)


def cache_bot_performance(bot_id: int, period: str, data: Dict[str, Any]) -> bool:
    """Cache bot performance data."""
    key = cache_key("analytics:bot_performance", bot_id=bot_id, period=period)
    return set_cached_data(key, data, ttl=600)  # 10 minutes


def get_cached_bot_performance(bot_id: int, period: str) -> Optional[Dict[str, Any]]:
    """Get cached bot performance data."""
    key = cache_key("analytics:bot_performance", bot_id=bot_id, period=period)
    return get_cached_data(key)


def cache_delivery_rates(start_date: str, end_date: str, bot_id: Optional[int], granularity: str, data: Dict[str, Any]) -> bool:
    """Cache delivery rates data."""
    key = cache_key("analytics:delivery_rates", start_date=start_date, end_date=end_date, bot_id=bot_id, granularity=granularity)
    return set_cached_data(key, data, ttl=600)  # 10 minutes


def get_cached_delivery_rates(start_date: str, end_date: str, bot_id: Optional[int], granularity: str) -> Optional[Dict[str, Any]]:
    """Get cached delivery rates data."""
    key = cache_key("analytics:delivery_rates", start_date=start_date, end_date=end_date, bot_id=bot_id, granularity=granularity)
    return get_cached_data(key)


def invalidate_analytics_cache(bot_id: Optional[int] = None) -> int:
    """Invalidate analytics cache entries."""
    patterns = [
        "analytics:overview:*",
        "analytics:trends:*",
        "analytics:delivery_rates:*",
        "analytics:active_contacts:*",
        "analytics:message_distribution:*"
    ]
    
    if bot_id:
        patterns.append(f"analytics:bot_performance:bot_id:{bot_id}:*")
    
    total_deleted = 0
    for pattern in patterns:
        total_deleted += invalidate_cache_pattern(pattern)
    
    logger.info(f"Invalidated {total_deleted} analytics cache entries")
    return total_deleted


def cache_active_contacts_stats(period: str, bot_id: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache active contacts statistics."""
    key = cache_key("analytics:active_contacts", period=period, bot_id=bot_id)
    return set_cached_data(key, data, ttl=600)  # 10 minutes


def get_cached_active_contacts_stats(period: str, bot_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Get cached active contacts statistics."""
    key = cache_key("analytics:active_contacts", period=period, bot_id=bot_id)
    return get_cached_data(key)


def cache_message_distribution(period: str, bot_id: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache message distribution data."""
    key = cache_key("analytics:message_distribution", period=period, bot_id=bot_id)
    return set_cached_data(key, data, ttl=600)  # 10 minutes


def get_cached_message_distribution(period: str, bot_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Get cached message distribution data."""
    key = cache_key("analytics:message_distribution", period=period, bot_id=bot_id)
    return get_cached_data(key)


def warm_up_cache(bot_id: Optional[int] = None) -> Dict[str, int]:
    """Warm up analytics cache with common queries."""
    warmed_up = {}
    
    try:
        from .crud import get_overview_stats
        
        # Warm up overview stats for common periods
        periods = ["today", "7days", "30days"]
        for period in periods:
            try:
                stats = get_overview_stats(None, period, bot_id)  # We need to pass db session
                cache_overview_stats(period, bot_id, stats)
                warmed_up[f"overview:{period}"] = 1
            except Exception as e:
                logger.error(f"Failed to warm up overview cache for {period}: {e}")
                warmed_up[f"overview:{period}"] = 0
        
        logger.info(f"Warmed up analytics cache: {warmed_up}")
        return warmed_up
        
    except Exception as e:
        logger.error(f"Failed to warm up analytics cache: {e}")
        return {"error": 1}


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        client = get_redis_client()
        if not client:
            return {"status": "redis_unavailable"}
        
        info = client.info()
        analytics_keys = client.keys("analytics:*")
        
        return {
            "status": "healthy",
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "analytics_keys_count": len(analytics_keys),
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}
