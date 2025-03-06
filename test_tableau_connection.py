#!/usr/bin/env python3
"""
Test script to verify the Tableau connection using PAT authentication.
"""

import logging
import sys
from fetch_tableau_data import TableauDataFetcher
from dotenv import load_dotenv
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_tableau_connection():
    """Test connection to Tableau Server and data fetching."""
    # Load environment variables
    load_dotenv()
    
    # Create data fetcher
    fetcher = TableauDataFetcher()
    
    # Display configuration
    logger.info(f"Base URL: {fetcher.base_url}")
    logger.info(f"API Version: {fetcher.api_version}")
    logger.info(f"Site ID: {fetcher.site_id}")
    logger.info(f"Token Name: {os.getenv('TABLEAU_API_TOKEN_NAME')}")
    
    # Get authentication token
    logger.info("Attempting to authenticate...")
    token = fetcher.get_token()
    
    if not token:
        logger.error("Authentication failed!")
        return False
    
    logger.info("Authentication successful!")
    
    # Test data fetching with a view ID
    view_id = input("Enter a Tableau View ID to test data fetching (or press Enter to skip): ")
    
    if view_id:
        logger.info(f"Fetching data for view ID: {view_id}")
        data = fetcher.fetch_view_data(view_id)
        
        if "error" in data:
            logger.error(f"Error fetching data: {data['error']}")
            return False
        
        logger.info("Data fetched successfully!")
        logger.info(f"Data preview: {json.dumps(data, indent=2)[:500]}...")
    
    return True

if __name__ == "__main__":
    logger.info("Testing Tableau connection...")
    success = test_tableau_connection()
    
    if success:
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)