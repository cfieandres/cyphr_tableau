#!/usr/bin/env python3
"""
Test script to verify the Snowflake Cortex connection.
"""

import logging
import sys
from snowflake_llm_processor import SnowflakeLLMProcessor
from dotenv import load_dotenv
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_snowflake_connection():
    """Test connection to Snowflake and Cortex functions."""
    # Load environment variables
    load_dotenv()
    
    # Display configuration
    logger.info(f"Account: {os.getenv('SNOWFLAKE_ACCOUNT')}")
    logger.info(f"User: {os.getenv('SNOWFLAKE_USER')}")
    logger.info(f"Warehouse: {os.getenv('SNOWFLAKE_WAREHOUSE')}")
    logger.info(f"Database: {os.getenv('SNOWFLAKE_DATABASE')}")
    logger.info(f"Schema: {os.getenv('SNOWFLAKE_SCHEMA')}")
    logger.info(f"Role: {os.getenv('SNOWFLAKE_ROLE')}")
    
    # Create LLM processor
    logger.info("Creating Snowflake LLM processor...")
    processor = SnowflakeLLMProcessor()
    
    try:
        # Test connection
        logger.info("Connecting to Snowflake...")
        processor.connect()
        logger.info("Connection successful!")
        
        # Test original process_query method
        logger.info("\n=== Testing process_query method ===")
        test_prompt = "Summarize the following data: [1, 2, 3, 4, 5]"
        
        logger.info(f"Sending test prompt: {test_prompt}")
        response = processor.process_query(
            query=test_prompt,
            model="claude-3-5-sonnet",
            temperature=0.7,
            max_tokens=500
        )
        
        if response and "Error" not in response:
            logger.info("process_query method succeeded!")
            logger.info(f"Response preview: {response[:200]}...")
        else:
            logger.error(f"process_query method failed: {response}")
            return False
        
        # Test cortex_handler compatible method
        logger.info("\n=== Testing process_data_with_cortex method ===")
        test_data = {"numbers": [1, 2, 3, 4, 5], "labels": ["A", "B", "C", "D", "E"]}
        test_system_message = "You are a helpful assistant. Analyze the data and provide insights."
        
        logger.info(f"Sending test data: {test_data}")
        logger.info(f"System message: {test_system_message}")
        
        try:
            result, metadata = processor.process_data_with_cortex(
                data=str(test_data),
                model_name="claude-3-5-sonnet",
                system_message=test_system_message,
                temperature=0.7,
                max_tokens=500,
                metadata={"test_run": True}
            )
            
            logger.info("process_data_with_cortex method succeeded!")
            logger.info(f"Result preview: {result[:200]}...")
            logger.info(f"Metadata: {json.dumps(metadata, indent=2)}")
            
        except Exception as e:
            logger.error(f"process_data_with_cortex method failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Snowflake connection: {e}")
        return False
        
    finally:
        # Close connections
        processor.disconnect()
        logger.info("Snowflake connection closed")

if __name__ == "__main__":
    logger.info("Testing Snowflake Cortex connection...")
    success = test_snowflake_connection()
    
    if success:
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)