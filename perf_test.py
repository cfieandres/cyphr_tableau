#!/usr/bin/env python3
"""
Performance test for the cyphr AI Extension using Locust.

This script simulates load testing with multiple concurrent users
making requests to the API endpoints.

To run this test, you need to have Locust installed:
pip install locust

Then run the test with:
locust -f perf_test.py
"""

import json
import random
import time
from locust import HttpUser, task, between

# Sample test data
TEST_DATA = [
    {
        "data": json.dumps({
            "sales": [random.randint(100, 500) for _ in range(5)],
            "months": ["Jan", "Feb", "Mar", "Apr", "May"],
            "products": ["A", "B", "C"]
        }),
        "format_type": "bullet"
    },
    {
        "data": json.dumps({
            "inventory": [random.randint(10, 100) for _ in range(4)],
            "products": ["A", "B", "C", "D"],
            "warehouses": ["North", "South", "East", "West"]
        }),
        "format_type": "paragraph"
    },
    {
        "data": "What are the key metrics to track for sales performance?",
        "format_type": "auto"
    },
    {
        "data": "Summarize the inventory levels across all warehouses.",
        "format_type": "paragraph"
    }
]

# Task types for route endpoint
TASK_TYPES = ["analyze", "summarize", "general"]


class ApiUser(HttpUser):
    """Simulated user for load testing the API."""
    
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    @task(3)
    def test_analytics_endpoint(self):
        """Test the analytics endpoint."""
        # Select random test data
        data = random.choice(TEST_DATA)
        
        # Send request to analytics endpoint
        start_time = time.time()
        with self.client.post("/analytics", json=data, catch_response=True) as response:
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data and response_data["response"]:
                    response.success()
                    print(f"Analytics response in {duration:.2f}s: {response_data['response'][:50]}...")
                else:
                    response.failure("Empty or invalid response")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def test_summarization_endpoint(self):
        """Test the summarization endpoint."""
        # Select random test data
        data = random.choice(TEST_DATA)
        
        # Send request to summarization endpoint
        start_time = time.time()
        with self.client.post("/summarization", json=data, catch_response=True) as response:
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data and response_data["response"]:
                    response.success()
                    print(f"Summarization response in {duration:.2f}s: {response_data['response'][:50]}...")
                else:
                    response.failure("Empty or invalid response")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(1)
    def test_general_endpoint(self):
        """Test the general endpoint."""
        # Select random test data
        data = random.choice(TEST_DATA)
        
        # Send request to general endpoint
        start_time = time.time()
        with self.client.post("/general", json=data, catch_response=True) as response:
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data and response_data["response"]:
                    response.success()
                    print(f"General response in {duration:.2f}s: {response_data['response'][:50]}...")
                else:
                    response.failure("Empty or invalid response")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def test_route_endpoint(self):
        """Test the route endpoint."""
        # Select random test data and task type
        data = random.choice(TEST_DATA)
        task_type = random.choice(TASK_TYPES)
        
        # Create route request
        route_request = {
            "data": data["data"],
            "task_type": task_type,
            "format_type": data["format_type"]
        }
        
        # Send request to route endpoint
        start_time = time.time()
        with self.client.post("/route", json=route_request, catch_response=True) as response:
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                if "response" in response_data and response_data["response"]:
                    response.success()
                    print(f"Route ({task_type}) response in {duration:.2f}s: {response_data['response'][:50]}...")
                else:
                    response.failure("Empty or invalid response")
            else:
                response.failure(f"Failed with status code: {response.status_code}")


if __name__ == "__main__":
    # This script is designed to be run with the Locust command-line tool
    print("Please run this script using the Locust command-line tool:")
    print("locust -f perf_test.py --host=http://localhost:8000")
    print("Then open a browser to http://localhost:8089/ to start the test.")