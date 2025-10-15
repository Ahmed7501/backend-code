#!/usr/bin/env python3
"""
Example script demonstrating Automation Triggers usage with ChatBoost backend.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
BOT_ID = 1
FLOW_ID = 1
TEST_PHONE = "1234567890"


def create_keyword_trigger() -> Dict[str, Any]:
    """Create a keyword trigger."""
    trigger_data = {
        "name": "Welcome Keyword Trigger",
        "bot_id": BOT_ID,
        "flow_id": FLOW_ID,
        "trigger_type": "keyword",
        "keywords": ["hi", "hello", "hey", "start"],
        "match_type": "exact",
        "case_sensitive": False,
        "priority": 10,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/triggers/", json=trigger_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating keyword trigger: {response.text}")
        return {}


def create_event_trigger() -> Dict[str, Any]:
    """Create an event trigger."""
    trigger_data = {
        "name": "New Contact Event Trigger",
        "bot_id": BOT_ID,
        "flow_id": FLOW_ID,
        "trigger_type": "event",
        "event_type": "new_contact",
        "event_conditions": {"source": "whatsapp"},
        "priority": 5,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/triggers/", json=trigger_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating event trigger: {response.text}")
        return {}


def create_schedule_trigger() -> Dict[str, Any]:
    """Create a schedule trigger."""
    trigger_data = {
        "name": "Daily Reminder Schedule Trigger",
        "bot_id": BOT_ID,
        "flow_id": FLOW_ID,
        "trigger_type": "schedule",
        "schedule_type": "daily",
        "schedule_time": "09:00",
        "schedule_timezone": "UTC",
        "priority": 1,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/triggers/", json=trigger_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating schedule trigger: {response.text}")
        return {}


def test_keyword_trigger(trigger_id: int, test_message: str) -> Dict[str, Any]:
    """Test a keyword trigger."""
    test_data = {
        "test_message": test_message
    }
    
    response = requests.post(f"{BASE_URL}/triggers/{trigger_id}/test", json=test_data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error testing keyword trigger: {response.text}")
        return {}


def get_trigger_statistics() -> Dict[str, Any]:
    """Get trigger statistics."""
    response = requests.get(f"{BASE_URL}/triggers/statistics")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting trigger statistics: {response.text}")
        return {}


def get_trigger_logs(trigger_id: int) -> list:
    """Get trigger execution logs."""
    response = requests.get(f"{BASE_URL}/triggers/{trigger_id}/logs")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting trigger logs: {response.text}")
        return []


def get_all_triggers() -> list:
    """Get all triggers."""
    response = requests.get(f"{BASE_URL}/triggers/")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting triggers: {response.text}")
        return []


def simulate_incoming_message(phone: str, message: str) -> Dict[str, Any]:
    """Simulate an incoming WhatsApp message."""
    # This would normally come from WhatsApp webhook
    message_data = {
        "from": phone,
        "text": {"body": message},
        "type": "text",
        "id": f"test_msg_{int(time.time())}"
    }
    
    # In a real scenario, this would be handled by the WhatsApp webhook
    print(f"Simulating incoming message from {phone}: '{message}'")
    return message_data


def main():
    """Main function to demonstrate trigger system usage."""
    print("🚀 ChatBoost Automation Triggers Demo")
    print("=" * 50)
    
    # Step 1: Create keyword trigger
    print("\n1. Creating keyword trigger...")
    keyword_trigger = create_keyword_trigger()
    if keyword_trigger:
        keyword_trigger_id = keyword_trigger.get("id")
        print(f"✅ Keyword trigger created with ID: {keyword_trigger_id}")
    else:
        print("❌ Failed to create keyword trigger")
        return
    
    # Step 2: Create event trigger
    print("\n2. Creating event trigger...")
    event_trigger = create_event_trigger()
    if event_trigger:
        event_trigger_id = event_trigger.get("id")
        print(f"✅ Event trigger created with ID: {event_trigger_id}")
    else:
        print("❌ Failed to create event trigger")
    
    # Step 3: Create schedule trigger
    print("\n3. Creating schedule trigger...")
    schedule_trigger = create_schedule_trigger()
    if schedule_trigger:
        schedule_trigger_id = schedule_trigger.get("id")
        print(f"✅ Schedule trigger created with ID: {schedule_trigger_id}")
    else:
        print("❌ Failed to create schedule trigger")
    
    # Step 4: Test keyword trigger
    print(f"\n4. Testing keyword trigger with 'hello'...")
    test_result = test_keyword_trigger(keyword_trigger_id, "hello")
    if test_result:
        print(f"✅ Test result: {test_result}")
    
    # Step 5: Test with non-matching message
    print(f"\n5. Testing keyword trigger with 'goodbye'...")
    test_result = test_keyword_trigger(keyword_trigger_id, "goodbye")
    if test_result:
        print(f"✅ Test result: {test_result}")
    
    # Step 6: Simulate incoming messages
    print(f"\n6. Simulating incoming messages...")
    test_messages = ["hi", "hello", "hey", "start", "help", "goodbye"]
    
    for message in test_messages:
        simulate_incoming_message(TEST_PHONE, message)
        time.sleep(1)  # Small delay between messages
    
    # Step 7: Wait for processing
    print(f"\n7. Waiting for message processing...")
    time.sleep(3)
    
    # Step 8: Check trigger logs
    print(f"\n8. Checking trigger logs...")
    logs = get_trigger_logs(keyword_trigger_id)
    if logs:
        print(f"✅ Found {len(logs.get('logs', []))} log entries")
        for log in logs.get('logs', [])[:3]:  # Show first 3 logs
            print(f"  - {log.get('triggered_at')}: {log.get('matched_value')} - {log.get('success')}")
    
    # Step 9: Get trigger statistics
    print(f"\n9. Getting trigger statistics...")
    stats = get_trigger_statistics()
    if stats:
        print(f"✅ Trigger statistics:")
        print(f"  - Total triggers: {stats.get('total_triggers')}")
        print(f"  - Active triggers: {stats.get('active_triggers')}")
        print(f"  - Keyword triggers: {stats.get('keyword_triggers')}")
        print(f"  - Event triggers: {stats.get('event_triggers')}")
        print(f"  - Schedule triggers: {stats.get('schedule_triggers')}")
        print(f"  - Total executions: {stats.get('total_executions')}")
        print(f"  - Last 24h executions: {stats.get('last_24h_executions')}")
    
    # Step 10: Get all triggers
    print(f"\n10. Getting all triggers...")
    triggers = get_all_triggers()
    if triggers:
        print(f"✅ Found {len(triggers.get('triggers', []))} triggers:")
        for trigger in triggers.get('triggers', []):
            print(f"  - {trigger.get('name')} ({trigger.get('trigger_type')}) - Active: {trigger.get('is_active')}")
    
    print("\n🎉 Automation Triggers demo completed!")
    print("\nNext steps:")
    print("1. Start Redis server: redis-server")
    print("2. Start Celery worker: python celery_worker.py")
    print("3. Test with real WhatsApp messages")
    print("4. Create more complex trigger conditions")
    print("5. Monitor trigger performance and logs")


if __name__ == "__main__":
    main()
