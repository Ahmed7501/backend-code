#!/usr/bin/env python3
"""
Analytics Demo Script for ChatBoost Backend

This script demonstrates how to use the Analytics & Reporting API endpoints
to fetch insights about bot performance, message delivery rates, and user engagement.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class AnalyticsDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return JSON response."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {"error": str(e)}
    
    def get_analytics_overview(self, period: str = "7days", bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics overview for specified period."""
        params = {"period": period}
        if bot_id:
            params["bot_id"] = bot_id
        
        print(f"\n📊 Getting Analytics Overview ({period})...")
        return self.make_request("GET", "/analytics/overview", params=params)
    
    def get_analytics_trends(self, days: int = 7, bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics trends for specified number of days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        if bot_id:
            params["bot_id"] = bot_id
        
        print(f"\n📈 Getting Analytics Trends ({days} days)...")
        return self.make_request("GET", "/analytics/trends", params=params)
    
    def get_bot_performance(self, bot_id: int, period: str = "30days") -> Dict[str, Any]:
        """Get performance metrics for a specific bot."""
        params = {"period": period}
        
        print(f"\n🤖 Getting Bot Performance (Bot {bot_id}, {period})...")
        return self.make_request("GET", f"/analytics/bots/{bot_id}/performance", params=params)
    
    def get_delivery_rates(self, days: int = 7, bot_id: Optional[int] = None, granularity: str = "daily") -> Dict[str, Any]:
        """Get delivery rate statistics."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "granularity": granularity
        }
        if bot_id:
            params["bot_id"] = bot_id
        
        print(f"\n📬 Getting Delivery Rates ({granularity}, {days} days)...")
        return self.make_request("GET", "/analytics/delivery-rates", params=params)
    
    def get_active_contacts_stats(self, period: str = "7days", bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get active contacts statistics."""
        params = {"period": period}
        if bot_id:
            params["bot_id"] = bot_id
        
        print(f"\n👥 Getting Active Contacts Stats ({period})...")
        return self.make_request("GET", "/analytics/active-contacts", params=params)
    
    def get_message_distribution(self, period: str = "7days", bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get message type distribution."""
        params = {"period": period}
        if bot_id:
            params["bot_id"] = bot_id
        
        print(f"\n📱 Getting Message Distribution ({period})...")
        return self.make_request("GET", "/analytics/message-distribution", params=params)
    
    def trigger_manual_aggregation(self, date: Optional[str] = None, bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Manually trigger statistics aggregation."""
        data = {}
        if date:
            data["date"] = date
        if bot_id:
            data["bot_id"] = bot_id
        
        print(f"\n⚡ Triggering Manual Aggregation...")
        return self.make_request("POST", "/analytics/aggregate-now", json=data)
    
    def get_analytics_health(self) -> Dict[str, Any]:
        """Get analytics system health check."""
        print(f"\n🏥 Getting Analytics Health Check...")
        return self.make_request("GET", "/analytics/health")
    
    def print_response(self, response: Dict[str, Any], title: str = "Response"):
        """Pretty print API response."""
        print(f"\n{'='*50}")
        print(f"{title}")
        print(f"{'='*50}")
        print(json.dumps(response, indent=2, default=str))
    
    def run_comprehensive_demo(self, bot_id: Optional[int] = None):
        """Run comprehensive analytics demo."""
        print("🚀 Starting Analytics Demo")
        print("="*60)
        
        # 1. Health Check
        health = self.get_analytics_health()
        self.print_response(health, "Analytics Health Check")
        
        # 2. Overview Stats
        overview = self.get_analytics_overview("7days", bot_id)
        self.print_response(overview, "Analytics Overview (7 days)")
        
        # 3. Trends Analysis
        trends = self.get_analytics_trends(7, bot_id)
        self.print_response(trends, "Analytics Trends (7 days)")
        
        # 4. Bot Performance (if bot_id provided)
        if bot_id:
            performance = self.get_bot_performance(bot_id, "30days")
            self.print_response(performance, f"Bot {bot_id} Performance (30 days)")
        
        # 5. Delivery Rates
        delivery_rates = self.get_delivery_rates(7, bot_id, "daily")
        self.print_response(delivery_rates, "Delivery Rates (Daily)")
        
        # 6. Active Contacts
        active_contacts = self.get_active_contacts_stats("7days", bot_id)
        self.print_response(active_contacts, "Active Contacts Stats (7 days)")
        
        # 7. Message Distribution
        message_dist = self.get_message_distribution("7days", bot_id)
        self.print_response(message_dist, "Message Distribution (7 days)")
        
        print("\n✅ Analytics Demo Complete!")
    
    def run_quick_demo(self, bot_id: Optional[int] = None):
        """Run quick analytics demo with key metrics."""
        print("⚡ Quick Analytics Demo")
        print("="*40)
        
        # Get overview
        overview = self.get_analytics_overview("today", bot_id)
        if "error" not in overview:
            print(f"\n📊 Today's Overview:")
            print(f"   Total Messages: {overview.get('total_messages', 0)}")
            print(f"   Active Contacts: {overview.get('active_contacts', 0)}")
            print(f"   Delivery Rate: {overview.get('delivery_rate', 0)}%")
            print(f"   Flow Completion: {overview.get('flow_completion_rate', 0)}%")
            
            # Show trends
            trends = overview.get('trends', {})
            if trends:
                print(f"\n📈 Trends:")
                for key, value in trends.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}%")
        
        # Get delivery rates
        delivery = self.get_delivery_rates(1, bot_id)
        if "error" not in delivery:
            print(f"\n📬 Delivery Summary:")
            print(f"   Average Rate: {delivery.get('average_delivery_rate', 0)}%")
            print(f"   Total Sent: {delivery.get('total_sent', 0)}")
            print(f"   Total Delivered: {delivery.get('total_delivered', 0)}")
        
        print("\n✅ Quick Demo Complete!")


def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analytics Demo for ChatBoost Backend")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--bot-id", type=int, help="Bot ID to analyze")
    parser.add_argument("--quick", action="store_true", help="Run quick demo only")
    parser.add_argument("--aggregate", action="store_true", help="Trigger manual aggregation")
    
    args = parser.parse_args()
    
    demo = AnalyticsDemo(args.url)
    
    if args.aggregate:
        # Trigger manual aggregation
        result = demo.trigger_manual_aggregation(bot_id=args.bot_id)
        demo.print_response(result, "Manual Aggregation Result")
    elif args.quick:
        # Run quick demo
        demo.run_quick_demo(args.bot_id)
    else:
        # Run comprehensive demo
        demo.run_comprehensive_demo(args.bot_id)


if __name__ == "__main__":
    main()
