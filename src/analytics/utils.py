"""
Helper utilities for analytics calculations and formatting.
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


def calculate_growth_percentage(current: float, previous: float) -> float:
    """Calculate percentage change between current and previous values."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_period_dates(period: str) -> Tuple[datetime, datetime]:
    """Convert period string to date range."""
    end_date = datetime.utcnow()
    
    if period == "today":
        start_date = datetime.combine(end_date.date(), datetime.min.time())
    elif period == "7days":
        start_date = end_date - timedelta(days=7)
    elif period == "30days":
        start_date = end_date - timedelta(days=30)
    elif period == "90days":
        start_date = end_date - timedelta(days=90)
    else:
        raise ValueError(f"Unsupported period: {period}")
    
    return start_date, end_date


def format_trend_data(stats: List[Dict[str, Any]], metric: str) -> List[Dict[str, Any]]:
    """Format data for trend visualization."""
    trend_data = []
    
    for stat in stats:
        if metric in stat:
            trend_data.append({
                "date": stat.get("date", ""),
                "value": stat[metric]
            })
    
    return trend_data


def calculate_moving_average(data: List[float], window: int = 7) -> List[float]:
    """Calculate moving average for a list of values."""
    if len(data) < window:
        return data
    
    moving_avg = []
    for i in range(len(data)):
        if i < window - 1:
            moving_avg.append(data[i])
        else:
            window_data = data[i - window + 1:i + 1]
            moving_avg.append(round(sum(window_data) / len(window_data), 2))
    
    return moving_avg


def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[Dict[str, Any]]:
    """Detect unusual patterns in data using statistical methods."""
    if len(data) < 3:
        return []
    
    anomalies = []
    mean_value = statistics.mean(data)
    stdev_value = statistics.stdev(data) if len(data) > 1 else 0
    
    for i, value in enumerate(data):
        if stdev_value > 0:
            z_score = abs((value - mean_value) / stdev_value)
            if z_score > threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": round(z_score, 2),
                    "severity": "high" if z_score > 3 else "medium"
                })
    
    return anomalies


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile value from a list of numbers."""
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def calculate_correlation(x_data: List[float], y_data: List[float]) -> float:
    """Calculate correlation coefficient between two datasets."""
    if len(x_data) != len(y_data) or len(x_data) < 2:
        return 0.0
    
    n = len(x_data)
    sum_x = sum(x_data)
    sum_y = sum(y_data)
    sum_xy = sum(x * y for x, y in zip(x_data, y_data))
    sum_x2 = sum(x * x for x in x_data)
    sum_y2 = sum(y * y for y in y_data)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
    
    if denominator == 0:
        return 0.0
    
    return round(numerator / denominator, 3)


def format_delivery_rate(sent: int, delivered: int) -> float:
    """Calculate and format delivery rate."""
    if sent == 0:
        return 0.0
    return round((delivered / sent) * 100, 2)


def format_flow_completion_rate(started: int, completed: int) -> float:
    """Calculate and format flow completion rate."""
    if started == 0:
        return 0.0
    return round((completed / started) * 100, 2)


def calculate_response_time_stats(response_times: List[float]) -> Dict[str, float]:
    """Calculate response time statistics."""
    if not response_times:
        return {
            "average": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "min": 0.0,
            "max": 0.0
        }
    
    return {
        "average": round(statistics.mean(response_times), 2),
        "median": round(statistics.median(response_times), 2),
        "p95": round(calculate_percentile(response_times, 95), 2),
        "p99": round(calculate_percentile(response_times, 99), 2),
        "min": round(min(response_times), 2),
        "max": round(max(response_times), 2)
    }


def group_by_time_period(data: List[Dict[str, Any]], period: str) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by time period (hour, day, week, month)."""
    grouped = {}
    
    for item in data:
        if "date" not in item:
            continue
            
        date_value = item["date"]
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value)
        
        if period == "hour":
            key = date_value.strftime("%Y-%m-%d %H:00")
        elif period == "day":
            key = date_value.strftime("%Y-%m-%d")
        elif period == "week":
            # Get week start (Monday)
            week_start = date_value - timedelta(days=date_value.weekday())
            key = week_start.strftime("%Y-%m-%d")
        elif period == "month":
            key = date_value.strftime("%Y-%m")
        else:
            continue
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(item)
    
    return grouped


def calculate_seasonality(data: List[Dict[str, Any]], metric: str) -> Dict[str, float]:
    """Calculate seasonal patterns in data."""
    if not data:
        return {}
    
    # Group by day of week
    daily_patterns = {}
    for item in data:
        if "date" in item and metric in item:
            date_value = item["date"]
            if isinstance(date_value, str):
                date_value = datetime.fromisoformat(date_value)
            
            day_of_week = date_value.strftime("%A")
            if day_of_week not in daily_patterns:
                daily_patterns[day_of_week] = []
            daily_patterns[day_of_week].append(item[metric])
    
    # Calculate averages for each day
    seasonal_patterns = {}
    for day, values in daily_patterns.items():
        if values:
            seasonal_patterns[day] = round(statistics.mean(values), 2)
    
    return seasonal_patterns


def generate_insights(stats: Dict[str, Any]) -> List[str]:
    """Generate human-readable insights from analytics data."""
    insights = []
    
    # Message volume insights
    total_messages = stats.get("total_messages", 0)
    if total_messages > 1000:
        insights.append(f"High message volume: {total_messages} messages processed")
    elif total_messages < 100:
        insights.append(f"Low message volume: {total_messages} messages processed")
    
    # Delivery rate insights
    delivery_rate = stats.get("delivery_rate", 0)
    if delivery_rate > 95:
        insights.append(f"Excellent delivery rate: {delivery_rate}%")
    elif delivery_rate < 80:
        insights.append(f"Low delivery rate: {delivery_rate}% - consider investigating")
    
    # Flow completion insights
    flow_completion_rate = stats.get("flow_completion_rate", 0)
    if flow_completion_rate > 80:
        insights.append(f"High flow completion rate: {flow_completion_rate}%")
    elif flow_completion_rate < 50:
        insights.append(f"Low flow completion rate: {flow_completion_rate}% - flows may need optimization")
    
    # Active contacts insights
    active_contacts = stats.get("active_contacts", 0)
    if active_contacts > 500:
        insights.append(f"Large active user base: {active_contacts} contacts")
    elif active_contacts < 50:
        insights.append(f"Small active user base: {active_contacts} contacts")
    
    return insights
