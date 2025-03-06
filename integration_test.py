#!/usr/bin/env python3
"""
Integration test for the cyphr AI Extension.

This script tests the complete flow from data fetching to AI processing to response formatting.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the components to test
from submit_data import DataSubmitter
from snowflake_llm_processor import SnowflakeLLMProcessor
from format_response import format_response


class MockTableauDataFetcher:
    """Mock TableauDataFetcher for testing."""
    
    def __init__(self):
        self.auth_token = "mock-token"
        self.site_id = "mock-site"
    
    def get_token(self, *args, **kwargs):
        return "mock-token"
    
    def _ensure_authenticated(self):
        pass
    
    def fetch_view_data(self, view_id):
        """Return mock data based on the view ID."""
        if view_id == "sales-view":
            return {
                "data": {
                    "sales": [100, 200, 300, 400, 500],
                    "months": ["Jan", "Feb", "Mar", "Apr", "May"],
                    "products": ["A", "B", "C"]
                }
            }
        elif view_id == "inventory-view":
            return {
                "data": {
                    "inventory": [50, 75, 25, 100],
                    "products": ["A", "B", "C", "D"],
                    "warehouses": ["North", "South", "East", "West"]
                }
            }
        else:
            return {"error": f"Unknown view ID: {view_id}"}


class MockSnowflakeLLMProcessor:
    """Mock SnowflakeLLMProcessor for testing."""
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def process_query(self, query, model="claude", temperature=0.7, endpoint=None, agent_config=None):
        """Return mock response based on the query content."""
        if "Analyze" in query:
            return "Analysis shows that product A has the highest sales in May. There's an upward trend in overall sales."
        elif "summary" in query:
            return "Sales are growing month-over-month with product C showing the most consistent growth."
        else:
            return "I'm not sure how to interpret this data without more context."


class IntegrationTest(unittest.TestCase):
    """Integration test for the complete AI processing flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock tableau data fetcher
        self.tableau_patch = patch("submit_data.TableauDataFetcher", MockTableauDataFetcher)
        self.mock_tableau = self.tableau_patch.start()
        
        # Create an actual data submitter with the mock tableau data fetcher
        self.data_submitter = DataSubmitter()
        
        # Create a mock LLM processor
        self.llm_processor = MockSnowflakeLLMProcessor()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.tableau_patch.stop()
    
    def test_complete_flow(self):
        """Test the complete flow from data fetching to response formatting."""
        # 1. Fetch and prepare data
        view_id = "sales-view"
        data_string = self.data_submitter.fetch_and_prepare_data(view_id)
        
        # Verify data was fetched and prepared correctly
        self.assertIsInstance(data_string, str)
        self.assertIn("sales", data_string)
        self.assertIn("months", data_string)
        self.assertIn("products", data_string)
        
        # 2. Process the data with the LLM
        prompt = f"Analyze the following data:\n\n{data_string}"
        response = self.llm_processor.process_query(prompt, temperature=0.5)
        
        # Verify response was generated
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        
        # 3. Format the response
        formatted_response = format_response(response, format_type="auto")
        
        # Verify response was formatted
        self.assertIsInstance(formatted_response, str)
        self.assertGreater(len(formatted_response), 0)
        
        # Print the complete flow for manual inspection
        print("\n=== Integration Test Results ===")
        print(f"Input Data: {data_string[:100]}...")
        print(f"Raw Response: {response}")
        print(f"Formatted Response: {formatted_response}")
        
        # Assert the complete flow produced non-empty output
        self.assertGreater(len(formatted_response), 0)


if __name__ == "__main__":
    unittest.main()