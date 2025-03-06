import snowflake.connector
from snowflake.snowpark import Session
import os
import logging
import json
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

# Default connection parameters - would be overridden by environment variables
DEFAULT_CONNECTION_PARAMS = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", ""),
    "database": os.getenv("SNOWFLAKE_DATABASE", ""),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", ""),
    "role": os.getenv("SNOWFLAKE_ROLE", ""),
    "authenticator": "externalbrowser",
    "client_session_keep_alive": True,
    "client_store_temporary_credential": True
}

class SnowflakeLLMProcessor:
    """Handles communication with Claude via Snowflake Cortex AI functions."""
    
    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Initialize the Snowflake connection.
        
        Args:
            connection_params: Dictionary with Snowflake connection parameters.
                              If None, uses environment variables.
        """
        self.connection_params = connection_params or DEFAULT_CONNECTION_PARAMS
        self.session = None
    
    def connect(self):
        """Create a connection to Snowflake if not already connected."""
        if not self.session:
            logger.info("Creating new Snowpark session")
            
            # Create a Snowpark session - this is the only connection we'll use
            self.session = Session.builder.configs(self.connection_params).create()
            
            # Set all context parameters explicitly to ensure they're active
            try:
                # Track which SQL statement we're executing for better error messages
                current_command = "INITIAL STATE"
                
                try:
                    # Query current state before modifications
                    current_command = "SELECT CURRENT STATE"
                    logger.info("Checking current state before modifications...")
                    try:
                        current_state = self.session.sql("SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()").collect()
                        if current_state and len(current_state) > 0:
                            logger.info(f"Current state: WAREHOUSE={current_state[0][0]}, DATABASE={current_state[0][1]}, SCHEMA={current_state[0][2]}, ROLE={current_state[0][3]}")
                        else:
                            logger.warning("Unable to get current state")
                    except Exception as e:
                        logger.warning(f"Error getting current state: {str(e)}")
                        
                    # Hardcode ML_OPT_WH warehouse since it seems to be working in your environment
                    current_command = "USE WAREHOUSE ML_OPT_WH"
                    logger.info("Setting warehouse to ML_OPT_WH")
                    self.session.sql("USE WAREHOUSE ML_OPT_WH").collect()
                    
                    # Also set original warehouse from config if different
                    warehouse = self.connection_params.get('warehouse')
                    if warehouse and warehouse != "ML_OPT_WH":
                        current_command = f"USE WAREHOUSE {warehouse}"
                        logger.info(f"Also setting warehouse from config: {warehouse}")
                        self.session.sql(f"USE WAREHOUSE {warehouse}").collect()
                    
                    # Set database if provided
                    database = self.connection_params.get('database')
                    if database:
                        current_command = f"USE DATABASE {database}"
                        logger.info(f"Setting database to {database}")
                        self.session.sql(f"USE DATABASE {database}").collect()
                    
                    # Skip schema setup - not needed for Cortex functions
                    logger.info("Skipping schema setup - not needed for Cortex functions")
                    
                    # Set role if provided
                    role = self.connection_params.get('role')
                    if role:
                        current_command = f"USE ROLE {role}"
                        logger.info(f"Setting role to {role}")
                        self.session.sql(f"USE ROLE {role}").collect()
                        
                except Exception as e:
                    logger.error(f"Error executing '{current_command}': {str(e)}")
                    raise
                
                # Verify the session has an active warehouse
                warehouse_result = self.session.sql("SELECT CURRENT_WAREHOUSE()").collect()
                active_warehouse = warehouse_result[0][0] if warehouse_result else None
                if active_warehouse:
                    logger.info(f"Active warehouse confirmed: {active_warehouse}")
                else:
                    logger.error("No active warehouse in the session after setup!")
                
            except Exception as e:
                logger.error(f"Error setting up Snowpark session: {str(e)}")
                raise
    
    def disconnect(self):
        """Close the Snowflake connection if it exists."""
        if self.session:
            logger.info("Closing Snowpark session")
            self.session.close()
            self.session = None
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before sending to Claude.
        
        Args:
            text: The text to preprocess
            
        Returns:
            The preprocessed text
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple newlines with a single newline
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def process_query(
        self, 
        prompt,  # Used as positional arg in main.py
        temperature=0.7,
        endpoint=None,
        agent_config=None,
        model="claude-3-5-sonnet", 
        max_tokens=4096,
        **kwargs  # Add **kwargs to catch any other arguments
    ) -> str:
        # Set module name for proper logging identification
        logger_name = __name__
        logger = logging.getLogger(logger_name)
        """
        Process a query using Claude via Snowflake Cortex.
        
        Args:
            prompt: The prompt text to send to Claude
            temperature: The temperature parameter for the model (default: 0.7)
            endpoint: The endpoint being used (for config lookup)
            agent_config: Optional agent configuration manager
            model: The model to use (default: claude-3-5-sonnet)
            max_tokens: Maximum tokens for response (default: 4096)
            
        Returns:
            The response from Claude
        """
        try:
            # Build metadata dictionary
            metadata = {"endpoint": endpoint} if endpoint else {}
            
            # Apply agent-specific settings if provided
            system_message = ""
            if endpoint and agent_config:
                from agent_config import AgentConfig
                if isinstance(agent_config, AgentConfig):
                    config = agent_config.get_config(endpoint)
                    if config:
                        # Use the agent's settings
                        model = config.model
                        temperature = config.temperature
                        system_message = config.instructions if config.instructions else ""
                        
                        # Add config details to metadata
                        metadata["agent_id"] = config.agent_id
                        metadata["config_id"] = f"{endpoint}_{config.agent_id}"
            
            # Preprocess the prompt
            processed_prompt = self.preprocess_text(prompt)
            
            # Connect to Snowflake
            self.connect()
            
            # Construct full prompt with system message if available
            if system_message:
                final_prompt = f"System: {system_message}\n\n{processed_prompt}"
            else:
                final_prompt = processed_prompt
            
            logger.info(f"Processing data with model: {model}")
            logger.debug(f"Temperature: {temperature}, Max Tokens: {max_tokens}")
            logger.info("SQL Query:")
            logger.info(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{model}',
                '{final_prompt}'
            ) AS processed_result
            """)
            
            # Escape single quotes in the prompt to avoid SQL injection
            safe_prompt = final_prompt.replace("'", "''")
            
            # Direct call to Cortex function - simpler syntax
            sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{safe_prompt}') AS processed_result
            """
            
            # Log the SQL query execution
            logger.info(f"Executing SQL with model={model}")
            logger.info(f"SQL (first 200 chars): {sql}...")
            
            # Explicitly set warehouse before every query execution
            try:
                logger.info("Setting ML_OPT_WH warehouse before Cortex query")
                self.session.sql('USE WAREHOUSE ML_OPT_WH').collect()
                
                # Verify basic connectivity
                logger.info("Testing basic Snowflake connectivity...")
                try:
                    self.session.sql("SELECT CURRENT_USER(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_ROLE()").collect()
                    logger.info("Successfully connected to Snowflake")
                except Exception as e:
                    logger.warning(f"Basic connectivity check failed: {str(e)}")
            except Exception as e:
                logger.error(f"Error during Snowflake connectivity check: {str(e)}")
            
            # Log the exact SQL we're about to execute
            logger.info(f"Executing Cortex SQL: {sql}")
            
            # Execute query with just model and prompt parameters as literal strings
            try:
                result_df = self.session.sql(sql).collect()
                logger.info("Successfully executed Cortex query")
            except Exception as e:
                logger.error(f"Error executing Cortex query: {str(e)}")
                raise
            
            if not result_df:
                logger.error("Cortex processing returned no result")
                return "No response from Claude"
            
            result = result_df[0]['PROCESSED_RESULT']
            logger.info("Successfully processed data with Cortex")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing query: {error_msg}")
            return f"Error processing query: {error_msg}"
        finally:
            # Snowpark sessions are expensive, so we'll only disconnect on explicit calls
            # or when the application terminates
            pass
    
    def process_data_with_cortex(
        self,
        data: str,
        model_name: str,
        system_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process data using Snowflake's Cortex LLM service (compatible with cortex_handler).
        
        Args:
            data (str): The data to be processed
            model_name (str): Name of the model to use (e.g., 'claude-3-5-sonnet')
            system_message (str): System message/prompt for the model
            temperature (float, optional): Model temperature. Defaults to 0.7
            max_tokens (int, optional): Maximum tokens for response. Defaults to 4096
            metadata (Dict[str, Any], optional): Additional metadata to include in response
            
        Returns:
            Tuple[str, Dict[str, Any]]: Processed result and metadata
        """
        try:
            # Connect to Snowflake if not already connected
            self.connect()
            
            # Log environment details before executing
            logger.info(f"Environment check before execution:")
            try:
                db_df = self.session.sql("SELECT CURRENT_DATABASE()").collect()
                warehouse_df = self.session.sql("SELECT CURRENT_WAREHOUSE()").collect()
                schema_df = self.session.sql("SELECT CURRENT_SCHEMA()").collect()
                role_df = self.session.sql("SELECT CURRENT_ROLE()").collect()
                
                current_db = db_df[0][0] if db_df else "Unknown"
                current_warehouse = warehouse_df[0][0] if warehouse_df else "Unknown"
                current_schema = schema_df[0][0] if schema_df else "Unknown"
                current_role = role_df[0][0] if role_df else "Unknown"
                
                logger.info(f"Database: {current_db}, Warehouse: {current_warehouse}, Schema: {current_schema}, Role: {current_role}")
                
                
                # Try to verify if the CORTEX.COMPLETE function exists
                logger.info("Checking if COMPLETE function exists...")
                try:
                    check_df = self.session.sql("SHOW FUNCTIONS LIKE 'COMPLETE' IN SCHEMA SNOWFLAKE.CORTEX").collect()
                    if check_df and len(check_df) > 0:
                        logger.info("SNOWFLAKE.CORTEX.COMPLETE function exists.")
                    else:
                        logger.warning("SNOWFLAKE.CORTEX.COMPLETE function not found in SHOW FUNCTIONS.")
                except Exception as e:
                    logger.warning(f"Error checking function existence: {str(e)}")
            except Exception as e:
                logger.warning(f"Error during environment check: {str(e)}")
            
            # Create system message and user prompt
            prompt = f"System: {system_message}\n\n{data}"
            
            # Direct call to Cortex function - simpler syntax
            logger.info("Using SNOWFLAKE.CORTEX.COMPLETE function")
            # Escape single quotes in the prompt
            safe_prompt = prompt.replace("'", "''")
            sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('{model_name}', '{safe_prompt}') AS processed_result
            """
            
            logger.info(f"Executing SQL with model={model_name}")
            logger.info(f"SQL (first 200 chars): {sql}...")
            
            # Explicitly set warehouse before every query execution
            try:
                logger.info("Setting ML_OPT_WH warehouse before Cortex query")
                self.session.sql('USE WAREHOUSE ML_OPT_WH').collect()
                
                # Verify basic connectivity
                logger.info("Testing basic Snowflake connectivity...")
                try:
                    connection_info = self.session.sql("SELECT CURRENT_USER(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_ROLE()").collect()
                    if connection_info and len(connection_info) > 0:
                        logger.info(f"Connected as: USER={connection_info[0][0]}, WAREHOUSE={connection_info[0][1]}, DATABASE={connection_info[0][2]}, ROLE={connection_info[0][3]}")
                    else:
                        logger.warning("Could not retrieve connection information")
                except Exception as e:
                    logger.warning(f"Basic connectivity check failed: {str(e)}")
            except Exception as e:
                logger.error(f"Error during Snowflake connectivity check: {str(e)}")
                
            # Log the exact SQL we're about to execute
            logger.info(f"Executing Cortex SQL: {sql}")
            
            # Execute query with direct string literals
            try:
                result_df = self.session.sql(sql).collect()
                logger.info("Successfully executed Cortex query")
            except Exception as e:
                logger.error(f"Error executing Cortex query: {str(e)}")
                raise
            
            if not result_df:
                raise Exception("Cortex processing returned no result")
            
            result = result_df[0]['PROCESSED_RESULT']
            
            # Get current user and database
            user_df = self.session.sql("SELECT CURRENT_USER()").collect()
            db_df = self.session.sql("SELECT CURRENT_DATABASE()").collect()
            current_user_val = user_df[0][0]
            current_db_val = db_df[0][0]
            
            # Prepare response metadata
            response_metadata = {
                'model_name': model_name,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'run_by': current_user_val,
                'run_environment': current_db_val
            }
            
            # Include additional metadata if provided
            if metadata:
                response_metadata.update(metadata)
            
            logger.info("Successfully processed data with Cortex")
            
            return result, response_metadata
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing data with Cortex: {error_msg}")
            raise


# Example usage
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Sample data to test with
    test_data = {"numbers": [1, 2, 3], "labels": ["A", "B", "C"]}
    
    # Create processor
    processor = SnowflakeLLMProcessor()
    
    # Test the standard process_query method
    print("\n=== Testing process_query method ===")
    query = f"Summarize this data: {test_data}"
    response = processor.process_query(
        query,
        temperature=0.7,
        model="claude-3-5-sonnet", 
        max_tokens=1000
    )
    print(f"Query: {query[:50]}...")
    print(f"Response: {response[:200]}...")
    
    # Test the cortex_handler compatible method
    print("\n=== Testing process_data_with_cortex method ===")
    try:
        result, metadata = processor.process_data_with_cortex(
            data=str(test_data),
            model_name="claude-3-5-sonnet",
            system_message="You are a helpful assistant. Analyze the data and provide insights.",
            temperature=0.7,
            max_tokens=1000,
            metadata={"test_run": True}
        )
        print(f"Result: {result[:200]}...")
        print(f"Metadata: {metadata}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Close connections
    processor.disconnect()
    print("\nTest complete.")