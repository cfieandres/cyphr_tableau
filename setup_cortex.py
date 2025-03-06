#!/usr/bin/env python3
"""
Script to set up Snowflake Cortex AI functions for the cyphr AI Extension.
This script creates the necessary SQL functions to interact with Claude via
Snowflake Cortex AI.
"""

import snowflake.connector
import os
from dotenv import load_dotenv
import argparse

load_dotenv()
# Add debug prints for environment variables
print("Environment variables loaded:")
print(f"SNOWFLAKE_ACCOUNT: {os.getenv('SNOWFLAKE_ACCOUNT')}")
print(f"SNOWFLAKE_USER: {os.getenv('SNOWFLAKE_USER')}")
print(f"SNOWFLAKE_WAREHOUSE: {os.getenv('SNOWFLAKE_WAREHOUSE')}")
print(f"SNOWFLAKE_DATABASE: {os.getenv('SNOWFLAKE_DATABASE')}")
print(f"SNOWFLAKE_SCHEMA: {os.getenv('SNOWFLAKE_SCHEMA')}")
print(f"SNOWFLAKE_ROLE: {os.getenv('SNOWFLAKE_ROLE')}")

# Update connection parameters with better error handling
DEFAULT_CONNECTION_PARAMS = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "authenticator": "externalbrowser"
}



def connect_to_snowflake(connection_params):
    """Connect to Snowflake and return the connection."""
    print(f"Connecting to Snowflake account: {connection_params['account']}")
    return snowflake.connector.connect(**connection_params)


def setup_cortex_functions(conn):
    """Set up Cortex AI functions in Snowflake."""
    cursor = conn.cursor()
    
    # Create the database and schema if they don't exist
    database = DEFAULT_CONNECTION_PARAMS["database"]
    schema = DEFAULT_CONNECTION_PARAMS["schema"]
    
    print(f"Creating database {database} if it doesn't exist...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    
    print(f"Creating schema {schema} if it doesn't exist...")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}")
    
    print(f"Using database {database} and schema {schema}...")
    cursor.execute(f"USE DATABASE {database}")
    cursor.execute(f"USE SCHEMA {schema}")
    
    # Create the Cortex AI function for Claude
    print("Creating CORTEX.COMPLETE function...")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION CORTEX.COMPLETE(
        MODEL STRING,
        PROMPT STRING,
        TEMPERATURE FLOAT
    )
    RETURNS STRING
    AS $$
        -- This is a placeholder for the actual Snowflake Cortex function
        -- In a real implementation, this would call Snowflake's built-in Cortex functions
        -- which integrate with Claude
        SELECT CORTEX.COMPLETE_CLAUDE(
            MODEL_NAME => MODEL,
            PROMPT => PROMPT,
            TEMPERATURE => TEMPERATURE
        )
    $$
    """)
    
    # Create a test function for easier testing
    print("Creating test function...")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION CORTEX.TEST_CLAUDE()
    RETURNS STRING
    AS $$
        SELECT CORTEX.COMPLETE(
            MODEL => 'claude',
            PROMPT => 'Say hello to the cyphr AI Extension!',
            TEMPERATURE => 0.7
        )
    $$
    """)
    
    print("Functions created successfully!")
    cursor.close()


def main():
    """Main function to set up Cortex AI functions."""
    parser = argparse.ArgumentParser(description="Set up Snowflake Cortex AI functions")
    parser.add_argument("--account", help="Snowflake account")
    parser.add_argument("--user", help="Snowflake user")
    parser.add_argument("--password", help="Snowflake password")
    parser.add_argument("--warehouse", help="Snowflake warehouse")
    parser.add_argument("--database", help="Snowflake database")
    parser.add_argument("--schema", help="Snowflake schema")
    parser.add_argument("--role", help="Snowflake role")
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise use environment variables
    connection_params = DEFAULT_CONNECTION_PARAMS.copy()
    for param in connection_params:
        arg_value = getattr(args, param, None)
        if arg_value:
            connection_params[param] = arg_value
    
    # Check if all required parameters are provided
    missing_params = [param for param, value in connection_params.items() 
                     if not value and param != 'schema']  # schema is optional
    
    if missing_params:
        print(f"Error: Missing required connection parameters: {', '.join(missing_params)}")
        print("Please provide them as command line arguments or set them in the .env file.")
        return
    
    try:
        # Connect to Snowflake
        conn = connect_to_snowflake(connection_params)
        
        # Set up Cortex AI functions
        setup_cortex_functions(conn)
        
        # Close the connection
        conn.close()
        
        print("Snowflake Cortex AI functions set up successfully!")
        
    except Exception as e:
        print(f"Error setting up Cortex AI functions: {e}")


if __name__ == "__main__":
    main()
