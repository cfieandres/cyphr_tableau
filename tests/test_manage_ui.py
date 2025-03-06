import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the FastAPI app and necessary components
from main import app
from agent_config import AgentConfig

# Create a test client
client = TestClient(app)

# Test data
TEST_CONFIG = {
    "endpoint": "/test-endpoint",
    "agent_id": "test-agent",
    "instructions": "Test instructions for the agent.",
    "model": "claude",
    "temperature": 0.5
}

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "test_agent_configs.json"
    return str(config_file)

@pytest.fixture
def app_with_temp_config(monkeypatch, temp_config_file):
    """Configure the app to use a temporary config file."""
    # Create a test config manager with the temp file
    test_config_manager = AgentConfig(config_file=temp_config_file)
    
    # Add test config
    test_config_manager.add_or_update_config(
        endpoint=TEST_CONFIG["endpoint"],
        agent_id=TEST_CONFIG["agent_id"],
        instructions=TEST_CONFIG["instructions"],
        model=TEST_CONFIG["model"],
        temperature=TEST_CONFIG["temperature"]
    )
    
    # Patch the app's config manager
    monkeypatch.setattr("main.agent_config_manager", test_config_manager)
    
    return test_config_manager


def test_get_manage_endpoint(app_with_temp_config):
    """Test that GET /manage returns HTML with endpoint list."""
    response = client.get("/manage")
    
    # Check response status
    assert response.status_code == 200
    
    # Check content type is HTML
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that the response contains expected HTML elements
    html_content = response.text
    assert "<title>cyphr AI Extension - Server Management</title>" in html_content
    assert "Endpoint Configurations" in html_content
    assert TEST_CONFIG["endpoint"] in html_content
    assert TEST_CONFIG["agent_id"] in html_content


def test_post_manage_configure(app_with_temp_config):
    """Test that POST /manage/configure updates config correctly."""
    # New config to add
    new_config = {
        "endpoint": "/new-test-endpoint",
        "agent_id": "new-test-agent",
        "instructions": "New test instructions for the agent.",
        "model": "claude",
        "temperature": 0.8
    }
    
    # Send POST request to configure endpoint
    response = client.post(
        "/manage/configure",
        json=new_config
    )
    
    # Check response status
    assert response.status_code == 200
    
    # Check response content
    data = response.json()
    assert data["status"] == "success"
    assert data["config"]["endpoint"] == new_config["endpoint"]
    assert data["config"]["agent_id"] == new_config["agent_id"]
    assert data["config"]["instructions"] == new_config["instructions"]
    assert data["config"]["model"] == new_config["model"]
    assert data["config"]["temperature"] == new_config["temperature"]
    
    # Check that the config was actually saved
    saved_config = app_with_temp_config.get_config(new_config["endpoint"])
    assert saved_config is not None
    assert saved_config.agent_id == new_config["agent_id"]
    assert saved_config.instructions == new_config["instructions"]
    assert saved_config.model == new_config["model"]
    assert saved_config.temperature == new_config["temperature"]


def test_update_existing_config(app_with_temp_config):
    """Test updating an existing configuration."""
    # Updated config
    updated_config = {
        "endpoint": TEST_CONFIG["endpoint"],  # Same endpoint to update
        "agent_id": "updated-agent-id",
        "instructions": "Updated instructions",
        "model": "claude-instant",
        "temperature": 0.9
    }
    
    # Send POST request to update endpoint
    response = client.post(
        "/manage/configure",
        json=updated_config
    )
    
    # Check response status
    assert response.status_code == 200
    
    # Check that the config was actually updated
    saved_config = app_with_temp_config.get_config(TEST_CONFIG["endpoint"])
    assert saved_config is not None
    assert saved_config.agent_id == updated_config["agent_id"]
    assert saved_config.instructions == updated_config["instructions"]
    assert saved_config.model == updated_config["model"]
    assert saved_config.temperature == updated_config["temperature"]