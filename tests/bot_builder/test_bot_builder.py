"""
Tests for bot builder module.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_bot(client: TestClient):
    """Test bot creation."""
    bot_data = {
        "name": "Test Bot",
        "description": "A test bot"
    }
    response = client.post("/bots/", json=bot_data)
    assert response.status_code == 201
    assert response.json()["name"] == bot_data["name"]
    assert response.json()["description"] == bot_data["description"]


def test_get_bots(client: TestClient):
    """Test getting all bots."""
    response = client.get("/bots/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_flow(client: TestClient):
    """Test flow creation."""
    # First create a bot
    bot_data = {
        "name": "Test Bot",
        "description": "A test bot"
    }
    bot_response = client.post("/bots/", json=bot_data)
    bot_id = bot_response.json()["id"]
    
    # Then create a flow
    flow_data = {
        "name": "Test Flow",
        "bot_id": bot_id,
        "structure": [
            {
                "node_type": "message",
                "content": {"text": "Hello!"}
            }
        ]
    }
    response = client.post("/bots/flows/", json=flow_data)
    assert response.status_code == 201
    assert response.json()["name"] == flow_data["name"]
    assert response.json()["bot_id"] == bot_id


def test_create_template(client: TestClient):
    """Test template creation."""
    template_data = {
        "name": "Test Template",
        "structure": [
            {
                "node_type": "message",
                "content": {"text": "Welcome!"}
            }
        ]
    }
    response = client.post("/bots/templates/", json=template_data)
    assert response.status_code == 201
    assert response.json()["name"] == template_data["name"]
