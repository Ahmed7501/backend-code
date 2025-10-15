#!/usr/bin/env python3
"""
Notifications Demo Script

This script demonstrates the Notifications API endpoints and WebSocket functionality for:
- Real-time WebSocket notifications
- Notification management
- Notification preferences
- Message status change notifications

Usage:
    python examples/notifications_demo.py --help
    python examples/notifications_demo.py --quick
    python examples/notifications_demo.py --websocket --token YOUR_JWT_TOKEN
"""

import argparse
import asyncio
import json
import logging
import sys
import websockets
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
API_BASE = f"{BASE_URL}/notifications"

# Demo data
DEMO_NOTIFICATION = {
    "title": "Demo Notification",
    "message": "This is a test notification from the demo script"
}

DEMO_PREFERENCES = {
    "email_enabled": True,
    "push_enabled": True,
    "message_status_enabled": True,
    "flow_events_enabled": True,
    "system_notifications_enabled": True
}


class NotificationsDemo:
    """Demo class for Notifications API and WebSocket."""
    
    def __init__(self, base_url: str = BASE_URL, ws_url: str = WS_URL):
        self.base_url = base_url
        self.ws_url = ws_url
        self.api_base = f"{base_url}/notifications"
        self.auth_base = f"{base_url}/auth"
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.organization_id: Optional[int] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
    
    def authenticate(self, email: str = "admin@example.com", password: str = "admin123") -> bool:
        """Authenticate and get access token."""
        try:
            # Login
            login_data = {
                "username": email,  # FastAPI OAuth2 uses 'username' field for email
                "password": password
            }
            
            response = self.session.post(
                f"{self.auth_base}/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{self.auth_base}/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    self.organization_id = user_data.get("organization_id")
                    logger.info(f"Authenticated as user {self.user_id}")
                    return True
                else:
                    logger.error("Failed to get user info")
                    return False
            else:
                logger.error(f"Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_notifications(self, skip: int = 0, limit: int = 50) -> Optional[list]:
        """Get user notifications."""
        try:
            response = self.session.get(
                f"{self.api_base}/",
                params={"skip": skip, "limit": limit}
            )
            
            if response.status_code == 200:
                notifications = response.json()
                logger.info(f"Retrieved {len(notifications)} notifications")
                return notifications
            else:
                logger.error(f"Failed to get notifications: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return None
    
    def get_unread_notifications(self) -> Optional[list]:
        """Get unread notifications."""
        try:
            response = self.session.get(f"{self.api_base}/unread")
            
            if response.status_code == 200:
                notifications = response.json()
                logger.info(f"Retrieved {len(notifications)} unread notifications")
                return notifications
            else:
                logger.error(f"Failed to get unread notifications: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting unread notifications: {e}")
            return None
    
    def get_notification_count(self) -> Optional[Dict[str, Any]]:
        """Get notification count."""
        try:
            response = self.session.get(f"{self.api_base}/count")
            
            if response.status_code == 200:
                count_data = response.json()
                logger.info(f"Notification count: {count_data['total']} total, {count_data['unread']} unread")
                return count_data
            else:
                logger.error(f"Failed to get notification count: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting notification count: {e}")
            return None
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read."""
        try:
            response = self.session.put(f"{self.api_base}/{notification_id}/read")
            
            if response.status_code == 200:
                logger.info(f"Marked notification {notification_id} as read")
                return True
            else:
                logger.error(f"Failed to mark notification as read: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_read(self) -> bool:
        """Mark all notifications as read."""
        try:
            response = self.session.put(f"{self.api_base}/read-all")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Marked {result['updated_count']} notifications as read")
                return True
            else:
                logger.error(f"Failed to mark all notifications as read: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False
    
    def get_notification_preferences(self) -> Optional[Dict[str, Any]]:
        """Get notification preferences."""
        try:
            response = self.session.get(f"{self.api_base}/preferences")
            
            if response.status_code == 200:
                preferences = response.json()
                logger.info("Retrieved notification preferences")
                return preferences
            else:
                logger.error(f"Failed to get notification preferences: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return None
    
    def update_notification_preferences(self, preferences: Dict[str, bool]) -> bool:
        """Update notification preferences."""
        try:
            response = self.session.put(
                f"{self.api_base}/preferences",
                json=preferences
            )
            
            if response.status_code == 200:
                logger.info("Updated notification preferences")
                return True
            else:
                logger.error(f"Failed to update notification preferences: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return False
    
    def get_notification_summary(self) -> Optional[Dict[str, Any]]:
        """Get notification summary."""
        try:
            response = self.session.get(f"{self.api_base}/summary")
            
            if response.status_code == 200:
                summary = response.json()
                logger.info(f"Notification summary: {summary['total']} total, {summary['unread']} unread")
                return summary
            else:
                logger.error(f"Failed to get notification summary: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting notification summary: {e}")
            return None
    
    def create_test_notification(self, title: str, message: str) -> bool:
        """Create a test notification."""
        try:
            response = self.session.post(
                f"{self.api_base}/test",
                params={"title": title, "message": message}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Created test notification: {result['notification_id']}")
                return True
            else:
                logger.error(f"Failed to create test notification: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating test notification: {e}")
            return False
    
    async def connect_websocket(self, token: str):
        """Connect to WebSocket for real-time notifications."""
        try:
            uri = f"{self.ws_url}/ws?token={token}"
            self.websocket = await websockets.connect(uri)
            
            logger.info("Connected to WebSocket")
            
            # Listen for messages
            async for message in self.websocket:
                data = json.loads(message)
                logger.info(f"Received WebSocket message: {data}")
                
                # Handle different message types
                if data.get("type") == "connected":
                    logger.info(f"WebSocket connected: {data['data']}")
                elif data.get("type") == "notification":
                    logger.info(f"New notification: {data['data']['title']}")
                elif data.get("type") == "pong":
                    logger.info("Received pong")
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
    
    async def send_websocket_message(self, message: Dict[str, Any]):
        """Send message via WebSocket."""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                logger.info(f"Sent WebSocket message: {message}")
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def ping_websocket(self):
        """Send ping to WebSocket."""
        await self.send_websocket_message({"type": "ping"})
    
    async def mark_read_via_websocket(self, notification_id: int):
        """Mark notification as read via WebSocket."""
        await self.send_websocket_message({
            "type": "mark_read",
            "notification_id": notification_id
        })
    
    async def mark_all_read_via_websocket(self):
        """Mark all notifications as read via WebSocket."""
        await self.send_websocket_message({"type": "mark_all_read"})
    
    async def get_unread_count_via_websocket(self):
        """Get unread count via WebSocket."""
        await self.send_websocket_message({"type": "get_unread_count"})
    
    def run_quick_demo(self):
        """Run a quick demonstration of notifications features."""
        logger.info("🚀 Starting Notifications Quick Demo")
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        # Get notification count
        logger.info("\n📊 Getting notification count...")
        count = self.get_notification_count()
        if count:
            logger.info(f"Total: {count['total']}, Unread: {count['unread']}")
            logger.info(f"By type: {count['by_type']}")
        
        # Get notifications
        logger.info("\n📋 Getting notifications...")
        notifications = self.get_notifications(limit=10)
        if notifications:
            for notif in notifications[:3]:  # Show first 3
                logger.info(f"  - {notif['title']} ({notif['type']}) - {'Read' if notif['is_read'] else 'Unread'}")
        
        # Get unread notifications
        logger.info("\n🔔 Getting unread notifications...")
        unread = self.get_unread_notifications()
        if unread:
            logger.info(f"Found {len(unread)} unread notifications")
        
        # Get notification preferences
        logger.info("\n⚙️ Getting notification preferences...")
        prefs = self.get_notification_preferences()
        if prefs:
            logger.info(f"Email enabled: {prefs['email_enabled']}")
            logger.info(f"Push enabled: {prefs['push_enabled']}")
            logger.info(f"Message status enabled: {prefs['message_status_enabled']}")
        
        # Get notification summary
        logger.info("\n📈 Getting notification summary...")
        summary = self.get_notification_summary()
        if summary:
            logger.info(f"Summary: {summary['total']} total, {summary['unread']} unread")
            logger.info(f"Recent notifications: {len(summary['recent'])}")
        
        # Create test notification
        logger.info("\n🧪 Creating test notification...")
        self.create_test_notification(
            "Demo Test",
            "This is a test notification created by the demo script"
        )
        
        logger.info("\n✅ Quick demo completed successfully!")
    
    async def run_websocket_demo(self, token: str):
        """Run WebSocket demonstration."""
        logger.info("🚀 Starting WebSocket Demo")
        
        try:
            # Connect to WebSocket
            await self.connect_websocket(token)
            
            # Send ping
            logger.info("\n📡 Sending ping...")
            await self.ping_websocket()
            await asyncio.sleep(1)
            
            # Get unread count
            logger.info("\n🔢 Getting unread count...")
            await self.get_unread_count_via_websocket()
            await asyncio.sleep(1)
            
            # Mark all as read
            logger.info("\n✅ Marking all as read...")
            await self.mark_all_read_via_websocket()
            await asyncio.sleep(1)
            
            # Keep connection alive for a bit
            logger.info("\n⏳ Keeping connection alive for 10 seconds...")
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"WebSocket demo error: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
    
    def run_comprehensive_demo(self):
        """Run a comprehensive demonstration."""
        logger.info("🚀 Starting Notifications Comprehensive Demo")
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        # Comprehensive notification management
        logger.info("\n📊 Comprehensive notification management...")
        
        # Get all notifications
        notifications = self.get_notifications(limit=100)
        if notifications:
            logger.info(f"Total notifications: {len(notifications)}")
            
            # Group by type
            by_type = {}
            for notif in notifications:
                by_type[notif['type']] = by_type.get(notif['type'], 0) + 1
            
            logger.info(f"Notifications by type: {by_type}")
        
        # Get unread notifications
        unread = self.get_unread_notifications()
        if unread:
            logger.info(f"\nUnread notifications ({len(unread)}):")
            for notif in unread[:5]:  # Show first 5
                logger.info(f"  - {notif['title']} ({notif['priority']})")
        
        # Get notification count
        count = self.get_notification_count()
        if count:
            logger.info(f"\nNotification counts:")
            logger.info(f"  Total: {count['total']}")
            logger.info(f"  Unread: {count['unread']}")
            logger.info(f"  By type: {count['by_type']}")
        
        # Get notification preferences
        prefs = self.get_notification_preferences()
        if prefs:
            logger.info(f"\nCurrent preferences:")
            logger.info(f"  Email: {prefs['email_enabled']}")
            logger.info(f"  Push: {prefs['push_enabled']}")
            logger.info(f"  Message status: {prefs['message_status_enabled']}")
            logger.info(f"  Flow events: {prefs['flow_events_enabled']}")
            logger.info(f"  System: {prefs['system_notifications_enabled']}")
        
        # Update preferences
        logger.info("\n⚙️ Updating notification preferences...")
        new_prefs = {
            "email_enabled": True,
            "push_enabled": False,
            "message_status_enabled": True,
            "flow_events_enabled": False,
            "system_notifications_enabled": True
        }
        self.update_notification_preferences(new_prefs)
        
        # Get notification summary
        summary = self.get_notification_summary()
        if summary:
            logger.info(f"\nNotification summary:")
            logger.info(f"  Total: {summary['total']}")
            logger.info(f"  Unread: {summary['unread']}")
            logger.info(f"  By type: {summary['by_type']}")
            logger.info(f"  Recent: {len(summary['recent'])} notifications")
        
        # Create multiple test notifications
        logger.info("\n🧪 Creating test notifications...")
        test_notifications = [
            ("System Alert", "This is a system alert notification"),
            ("Message Delivered", "Your message has been delivered"),
            ("Flow Completed", "Flow execution has completed successfully"),
            ("User Mention", "You were mentioned in a comment")
        ]
        
        for title, message in test_notifications:
            self.create_test_notification(title, message)
        
        # Mark some notifications as read
        if notifications:
            logger.info("\n✅ Marking some notifications as read...")
            for notif in notifications[:3]:  # Mark first 3 as read
                if not notif['is_read']:
                    self.mark_notification_read(notif['id'])
        
        # Get updated count
        logger.info("\n📊 Getting updated notification count...")
        updated_count = self.get_notification_count()
        if updated_count:
            logger.info(f"Updated counts: {updated_count['total']} total, {updated_count['unread']} unread")
        
        logger.info("\n✅ Comprehensive demo completed successfully!")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Notifications Demo")
    parser.add_argument("--quick", action="store_true", help="Run quick demo")
    parser.add_argument("--websocket", action="store_true", help="Run WebSocket demo")
    parser.add_argument("--token", help="JWT token for WebSocket demo")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for API")
    parser.add_argument("--ws-url", default=WS_URL, help="WebSocket URL")
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = NotificationsDemo(args.base_url, args.ws_url)
    
    try:
        if args.websocket:
            if not args.token:
                logger.error("❌ Token required for WebSocket demo")
                sys.exit(1)
            
            # Run WebSocket demo
            asyncio.run(demo.run_websocket_demo(args.token))
        elif args.quick:
            demo.run_quick_demo()
        else:
            demo.run_comprehensive_demo()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
