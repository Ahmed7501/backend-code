#!/usr/bin/env python3
"""
Example script demonstrating WhatsApp API usage with ChatBoost backend.
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
BOT_ID = 1  # You'll need to create a bot first

# Your WhatsApp credentials (from the user's request)
WHATSAPP_ACCESS_TOKEN = "EAASeqnctyV0BPqwVNaoZCwX9D1jrZClZC016sdIcu91dzO2ygx1heZA2Nla1ufuQTiZAYihLY9wnYVJeREZAjU4zRkEyaVdjrIPZCUGdPjEfOYTlxfiTbPa173wsGUqVZBTr7hMJCZBC2gseACZAwxCX0wa9fYCvPd3ZC6Ms5SVfMf62f77QHnmevKlLpzQ51v9GT1MahbzO7KOE4kD7JthgxUEuqIaXUHGbzG7foPkkyy1ShDePq8OezDgN10QVVYZAZCQZDZD"
WHATSAPP_PHONE_NUMBER_ID = "741568929049687"
WHATSAPP_BUSINESS_ACCOUNT_ID = "1263163798895472"
TEST_PHONE_NUMBER = "923127921278"  # From your example


def create_bot_with_whatsapp_credentials() -> Dict[str, Any]:
    """Create a bot with WhatsApp credentials."""
    bot_data = {
        "name": "WhatsApp Test Bot",
        "description": "Bot for testing WhatsApp integration",
        "is_whatsapp_enabled": True,
        "whatsapp_access_token": WHATSAPP_ACCESS_TOKEN,
        "whatsapp_phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "whatsapp_business_account_id": WHATSAPP_BUSINESS_ACCOUNT_ID
    }
    
    response = requests.post(f"{BASE_URL}/bots/", json=bot_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating bot: {response.text}")
        return {}


def send_template_message(bot_id: int, to: str) -> Dict[str, Any]:
    """Send a template message."""
    message_data = {
        "to": to,
        "template_name": "hello_world",
        "language_code": "en_US"
    }
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/send/template?bot_id={bot_id}",
        json=message_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error sending template message: {response.text}")
        return {}


def send_text_message(bot_id: int, to: str, text: str) -> Dict[str, Any]:
    """Send a text message."""
    message_data = {
        "to": to,
        "text": text
    }
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/send/text?bot_id={bot_id}",
        json=message_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error sending text message: {response.text}")
        return {}


def get_message_history(bot_id: int) -> Dict[str, Any]:
    """Get message history for a bot."""
    response = requests.get(f"{BASE_URL}/whatsapp/messages/{bot_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting message history: {response.text}")
        return {}


def main():
    """Main function to demonstrate WhatsApp API usage."""
    print("🚀 ChatBoost WhatsApp API Demo")
    print("=" * 50)
    
    # Step 1: Create a bot with WhatsApp credentials
    print("\n1. Creating bot with WhatsApp credentials...")
    bot = create_bot_with_whatsapp_credentials()
    if bot:
        bot_id = bot.get("id")
        print(f"✅ Bot created with ID: {bot_id}")
    else:
        print("❌ Failed to create bot")
        return
    
    # Step 2: Send a template message
    print(f"\n2. Sending template message to {TEST_PHONE_NUMBER}...")
    template_result = send_template_message(bot_id, TEST_PHONE_NUMBER)
    if template_result:
        print(f"✅ Template message sent: {template_result}")
    else:
        print("❌ Failed to send template message")
    
    # Step 3: Send a text message
    print(f"\n3. Sending text message to {TEST_PHONE_NUMBER}...")
    text_result = send_text_message(bot_id, TEST_PHONE_NUMBER, "Hello from ChatBoost! 🚀")
    if text_result:
        print(f"✅ Text message sent: {text_result}")
    else:
        print("❌ Failed to send text message")
    
    # Step 4: Get message history
    print(f"\n4. Getting message history for bot {bot_id}...")
    history = get_message_history(bot_id)
    if history:
        print(f"✅ Message history retrieved: {len(history.get('messages', []))} messages")
        print(f"Total messages: {history.get('total', 0)}")
    else:
        print("❌ Failed to get message history")
    
    print("\n🎉 Demo completed!")
    print("\nNext steps:")
    print("1. Set up webhook URL in Meta Developer Console")
    print("2. Configure webhook verification token in .env file")
    print("3. Test incoming message handling")


if __name__ == "__main__":
    main()
