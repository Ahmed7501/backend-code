#!/usr/bin/env python3
"""
Example script demonstrating Flow Engine usage with ChatBoost backend.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PHONE = "1234567890"
BOT_ID = 1


def create_test_flow() -> Dict[str, Any]:
    """Create a test flow for demonstration."""
    flow_data = {
        "name": "Welcome Flow",
        "bot_id": BOT_ID,
        "structure": [
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "Hello! Welcome to our bot. Please respond with 'yes' or 'no'."},
                    "next": 1
                }
            },
            {
                "type": "wait",
                "config": {
                    "duration": 30,
                    "unit": "seconds",
                    "next": 2
                }
            },
            {
                "type": "condition",
                "config": {
                    "variable": "state.user_response",
                    "operator": "==",
                    "value": "yes",
                    "true_path": 3,
                    "false_path": 4
                }
            },
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "Great! You said yes. Thank you for your response!"},
                    "next": None
                }
            },
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "You said no. That's okay too! Have a great day!"},
                    "next": None
                }
            }
        ]
    }
    return flow_data


def create_contact(phone_number: str) -> Dict[str, Any]:
    """Create a contact."""
    contact_data = {
        "phone_number": phone_number,
        "first_name": "Test",
        "last_name": "User",
        "metadata": {"source": "demo"}
    }
    
    response = requests.post(f"{BASE_URL}/flows/contacts/", json=contact_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating contact: {response.text}")
        return {}


def create_flow(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a flow."""
    response = requests.post(f"{BASE_URL}/bots/flows/", json=flow_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating flow: {response.text}")
        return {}


def start_flow_execution(flow_id: int, contact_phone: str) -> Dict[str, Any]:
    """Start a flow execution."""
    execution_data = {
        "flow_id": flow_id,
        "contact_phone": contact_phone,
        "bot_id": BOT_ID,
        "initial_state": {"demo_mode": True}
    }
    
    response = requests.post(f"{BASE_URL}/flows/execute", json=execution_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error starting flow execution: {response.text}")
        return {}


def send_user_input(execution_id: int, message: str) -> Dict[str, Any]:
    """Send user input to a flow execution."""
    input_data = {
        "execution_id": execution_id,
        "message": message,
        "message_type": "text"
    }
    
    response = requests.post(f"{BASE_URL}/flows/executions/{execution_id}/input", json=input_data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error sending user input: {response.text}")
        return {}


def get_execution_status(execution_id: int) -> Dict[str, Any]:
    """Get execution status."""
    response = requests.get(f"{BASE_URL}/flows/executions/{execution_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting execution status: {response.text}")
        return {}


def get_execution_logs(execution_id: int) -> list:
    """Get execution logs."""
    response = requests.get(f"{BASE_URL}/flows/executions/{execution_id}/logs")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting execution logs: {response.text}")
        return []


def main():
    """Main function to demonstrate Flow Engine usage."""
    print("🚀 ChatBoost Flow Engine Demo")
    print("=" * 50)
    
    # Step 1: Create contact
    print("\n1. Creating contact...")
    contact = create_contact(TEST_PHONE)
    if contact:
        print(f"✅ Contact created with ID: {contact.get('id')}")
    else:
        print("❌ Failed to create contact")
        return
    
    # Step 2: Create flow
    print("\n2. Creating test flow...")
    flow_data = create_test_flow()
    flow = create_flow(flow_data)
    if flow:
        flow_id = flow.get("id")
        print(f"✅ Flow created with ID: {flow_id}")
    else:
        print("❌ Failed to create flow")
        return
    
    # Step 3: Start flow execution
    print(f"\n3. Starting flow execution for {TEST_PHONE}...")
    execution = start_flow_execution(flow_id, TEST_PHONE)
    if execution:
        execution_id = execution.get("id")
        print(f"✅ Flow execution started with ID: {execution_id}")
    else:
        print("❌ Failed to start flow execution")
        return
    
    # Step 4: Wait for initial message to be sent
    print("\n4. Waiting for initial message to be sent...")
    time.sleep(2)
    
    # Step 5: Check execution status
    print(f"\n5. Checking execution status...")
    status = get_execution_status(execution_id)
    if status:
        print(f"✅ Execution status: {status.get('status')}")
        print(f"Current node index: {status.get('current_node_index')}")
    
    # Step 6: Send user input
    print(f"\n6. Sending user input 'yes'...")
    input_result = send_user_input(execution_id, "yes")
    if input_result:
        print(f"✅ User input processed: {input_result}")
    
    # Step 7: Wait and check final status
    print(f"\n7. Waiting for flow to complete...")
    time.sleep(3)
    
    final_status = get_execution_status(execution_id)
    if final_status:
        print(f"✅ Final execution status: {final_status.get('status')}")
    
    # Step 8: Get execution logs
    print(f"\n8. Getting execution logs...")
    logs = get_execution_logs(execution_id)
    if logs:
        print(f"✅ Found {len(logs)} log entries:")
        for log in logs:
            print(f"  - Node {log.get('node_index')}: {log.get('node_type')} - {log.get('action')}")
    
    # Step 9: Get execution statistics
    print(f"\n9. Getting execution statistics...")
    response = requests.get(f"{BASE_URL}/flows/statistics")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Execution statistics:")
        print(f"  - Total executions: {stats.get('total_executions')}")
        print(f"  - Running executions: {stats.get('running_executions')}")
        print(f"  - Completed executions: {stats.get('completed_executions')}")
        print(f"  - Total contacts: {stats.get('total_contacts')}")
    
    print("\n🎉 Flow Engine demo completed!")
    print("\nNext steps:")
    print("1. Start Redis server: redis-server")
    print("2. Start Celery worker: python celery_worker.py")
    print("3. Test with real WhatsApp messages")
    print("4. Create more complex flows with conditions and webhooks")


if __name__ == "__main__":
    main()
