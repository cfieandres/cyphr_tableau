import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the FastAPI app and necessary components
from main import app, FormatType
from snowflake_llm_processor import SnowflakeLLMProcessor

# Create a test client
client = TestClient(app)

# Mock responses for each endpoint
MOCK_ANALYTICS_RESPONSE = "Analysis of the data shows several key insights..."
MOCK_SUMMARIZATION_RESPONSE = "This is a summary of the provided data..."
MOCK_GENERAL_RESPONSE = "Here is the answer to your question..."


@pytest.fixture
def mock_llm_processor():
    """Create a mock LLM processor for testing."""
    with patch("main.llm_processor") as mock_processor:
        # Mock the process_query method
        mock_processor.process_query.side_effect = lambda prompt, temperature, endpoint, agent_config: {
            "/analytics": MOCK_ANALYTICS_RESPONSE,
            "/summarization": MOCK_SUMMARIZATION_RESPONSE,
            "/general": MOCK_GENERAL_RESPONSE
        }.get(endpoint, "Unknown endpoint")
        
        yield mock_processor


def test_analytics_endpoint(mock_llm_processor):
    """Test the analytics endpoint."""
    # Test data
    test_data = {
        "data": "{'sales': [100, 200, 300], 'dates': ['2023-01', '2023-02', '2023-03']}",
        "format_type": FormatType.BULLET
    }
    
    # Make a request to the analytics endpoint
    response = client.post("/analytics", json=test_data)
    
    # Check the response
    assert response.status_code == 200
    assert "response" in response.json()
    # Use 'in' operator to be more flexible with formatting differences
    assert MOCK_ANALYTICS_RESPONSE in response.json()["response"]
    
    # Verify the LLM processor was called correctly
    mock_llm_processor.process_query.assert_called_once()
    args, kwargs = mock_llm_processor.process_query.call_args
    # In real world usage, prompt is a positional arg, so check args[0] instead
    assert "Analyze the following data" in args[0]
    # Check kwargs as before
    assert kwargs["temperature"] == 0.5
    assert kwargs["endpoint"] == "/analytics"


def test_summarization_endpoint(mock_llm_processor):
    """Test the summarization endpoint."""
    # Test data
    test_data = {
        "data": "This is a long text that needs to be summarized. It contains many details...",
        "format_type": FormatType.PARAGRAPH
    }
    
    # Make a request to the summarization endpoint
    response = client.post("/summarization", json=test_data)
    
    # Check the response
    assert response.status_code == 200
    assert "response" in response.json()
    # Use 'in' operator to be more flexible with formatting differences
    assert MOCK_SUMMARIZATION_RESPONSE in response.json()["response"]
    
    # Verify the LLM processor was called correctly
    mock_llm_processor.process_query.assert_called_once()
    args, kwargs = mock_llm_processor.process_query.call_args
    # In real world usage, prompt is a positional arg, so check args[0] instead
    assert "Provide a concise summary" in args[0]
    # Check kwargs as before
    assert kwargs["temperature"] == 0.3
    assert kwargs["endpoint"] == "/summarization"


def test_general_endpoint(mock_llm_processor):
    """Test the general endpoint."""
    # Test data
    test_data = {
        "data": "What is the meaning of life?",
        "format_type": FormatType.AUTO
    }
    
    # Make a request to the general endpoint
    response = client.post("/general", json=test_data)
    
    # Check the response
    assert response.status_code == 200
    assert "response" in response.json()
    # Use 'in' operator to be more flexible with formatting differences
    assert MOCK_GENERAL_RESPONSE in response.json()["response"]
    
    # Verify the LLM processor was called correctly
    mock_llm_processor.process_query.assert_called_once()
    args, kwargs = mock_llm_processor.process_query.call_args
    # In real world usage, prompt is a positional arg, so check args[0] instead
    assert args[0] == test_data["data"]
    # Check kwargs as before
    assert kwargs["temperature"] == 0.7
    assert kwargs["endpoint"] == "/general"


def test_route_endpoint(mock_llm_processor):
    """Test the route endpoint."""
    # Test data
    test_data = {
        "data": "Please analyze this data: [1, 2, 3, 4, 5]",
        "task_type": "analyze",
        "format_type": FormatType.BULLET
    }
    
    # Make a request to the route endpoint
    response = client.post("/route", json=test_data)
    
    # Check the response
    assert response.status_code == 200
    assert "response" in response.json()
    # Use 'in' operator to be more flexible with formatting differences
    assert MOCK_ANALYTICS_RESPONSE in response.json()["response"]
    
    # Verify the LLM processor was called correctly
    mock_llm_processor.process_query.assert_called_once()
    args, kwargs = mock_llm_processor.process_query.call_args
    # In real world usage, prompt is a positional arg, so check args[0] instead
    assert "Analyze the following data" in args[0]
    # Check kwargs as before
    assert kwargs["temperature"] == 0.5
    assert kwargs["endpoint"] == "/analytics"


def test_anonymization(mock_llm_processor):
    """Test that sensitive data is anonymized."""
    # Test data with sensitive information
    test_data = {
        "data": "My email is test@example.com and my phone is 555-123-4567",
        "format_type": FormatType.AUTO
    }
    
    # Make a request to the analytics endpoint
    response = client.post("/analytics", json=test_data)
    
    # Check the response
    assert response.status_code == 200
    
    # Verify the LLM processor was called with anonymized data
    mock_llm_processor.process_query.assert_called_once()
    args, kwargs = mock_llm_processor.process_query.call_args
    # In real world usage, prompt is a positional arg, so check args[0] instead
    assert "test@example.com" not in args[0]
    assert "555-123-4567" not in args[0]
    assert "[EMAIL REDACTED]" in args[0]
    assert "[PHONE REDACTED]" in args[0]