"""
Test script for the API endpoints.
Use this script to test the API endpoints without a browser.
"""

import requests
import json
import sys

# Base URL for API
BASE_URL = "http://localhost:8000"

def test_endpoints_api():
    """Test the endpoints API."""
    print("\n=== Testing endpoints API ===")
    
    # Test GET /api/endpoints
    print("\nGET /api/endpoints")
    response = requests.get(f"{BASE_URL}/api/endpoints")
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('endpoints', []))} endpoints")
        for endpoint in data.get('endpoints', []):
            print(f"- {endpoint['name']} ({endpoint['endpoint']})")
    else:
        print(f"Error: {response.text}")
    
    # Test POST /api/endpoints
    print("\nPOST /api/endpoints")
    test_data = {
        "endpoint": "/test-endpoint",
        "agent_id": "test-agent",
        "name": "Test Endpoint",
        "description": "This is a test endpoint",
        "instructions": "Here are the instructions for the test endpoint.",
        "indicators": ["test", "endpoint"],
        "priority": 100,
        "model": "claude-3-5-sonnet",
        "temperature": 0.7
    }
    
    # Print the request data for debugging
    print(f"Sending data: {json.dumps(test_data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/endpoints", 
        json=test_data
    )
    
    print(f"Status code: {response.status_code}")
    if response.status_code in (200, 201):
        print(f"Success: {response.json()}")
    else:
        print(f"Error: {response.text}")
    
    # Test GET for the new endpoint
    print("\nGET /api/endpoints/test-endpoint")
    response = requests.get(f"{BASE_URL}/api/endpoints/test-endpoint")
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
    
    # Test DELETE the test endpoint
    print("\nDELETE /api/endpoints/test-endpoint")
    response = requests.delete(f"{BASE_URL}/api/endpoints/test-endpoint")
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"Success: {response.json()}")
    else:
        print(f"Error: {response.text}")

def test_dynamic_endpoint():
    """Test a dynamic endpoint."""
    print("\n=== Testing dynamic endpoint ===")
    
    # First create a test endpoint
    test_data = {
        "endpoint": "/dynamic-test",
        "agent_id": "dynamic-test-agent",
        "name": "Dynamic Test",
        "description": "This is a dynamic test endpoint",
        "instructions": "Return a summary of the provided information.",
        "indicators": ["dynamic", "test"],
        "priority": 100,
        "model": "claude-3-5-sonnet",
        "temperature": 0.7
    }
    
    print("\nCreating test endpoint...")
    response = requests.post(f"{BASE_URL}/api/endpoints", json=test_data)
    if response.status_code not in (200, 201):
        print(f"Error creating test endpoint: {response.text}")
        return
    
    # Now test the endpoint
    print("\nTesting dynamic endpoint...")
    test_request = {
        "data": "This is test data for the dynamic endpoint.",
        "format_type": "auto"
    }
    
    response = requests.post(f"{BASE_URL}/dynamic-test", json=test_request)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
    
    # Delete the test endpoint
    print("\nDeleting test endpoint...")
    requests.delete(f"{BASE_URL}/api/endpoints/dynamic-test")

if __name__ == "__main__":
    # Check which test to run
    if len(sys.argv) > 1 and sys.argv[1] == "dynamic":
        test_dynamic_endpoint()
    else:
        test_endpoints_api()