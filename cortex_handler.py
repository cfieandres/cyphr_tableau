import os
import json
from typing import Dict, Any, Tuple, Optional
from snowflake.snowpark import Session
from snowflake.snowpark.functions import current_user, current_database
import logging

logger = logging.getLogger(__name__)

def process_data_with_cortex(
    session: Session,
    data: str,
    model_name: str,
    system_message: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Process data using Snowflake's Cortex LLM service.

    Args:
        session (Session): An active Snowflake session
        data (str): The data to be processed
        model_name (str): Name of the model to use (e.g., 'claude-3-5-sonnet')
        system_message (str): System message/prompt for the model
        temperature (float, optional): Model temperature. Defaults to 0.7
        max_tokens (int, optional): Maximum tokens for response. Defaults to 4096
        metadata (Dict[str, Any], optional): Additional metadata to include in response

    Returns:
        Tuple[str, Dict[str, Any]]: Processed result and metadata

    Raises:
        Exception: If Cortex processing fails
    """
    try:
        # Create system message and user prompt
        prompt = f"System: {system_message}\n\n{data}"
        
        # Construct and execute Cortex query with temperature and max_tokens parameters
        sql = """
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            ?,    -- model
            ?,    -- prompt
            OBJECT_CONSTRUCT('temperature', ?, 'max_tokens', ?)
        ) AS processed_result
        """
        
        # Log the request to database if config_id is provided
        config_id = metadata.get("config_id") if metadata else None
        if config_id:
            log_sql = f"""
                INSERT INTO cyphr_execution_logs (config_id, log_level, message)
                VALUES ({config_id}, 'INFO', 'Processing data with model: {model_name}')
            """
            session.sql(log_sql).collect()
        else:
            logger.info(f"Processing data with model: {model_name}")
            logger.debug(f"Temperature: {temperature}, Max Tokens: {max_tokens}")
        
        # Execute query with temperature and max_tokens
        result_df = session.sql(sql, params=[model_name, prompt, temperature, max_tokens]).collect()
        
        if not result_df:
            raise Exception("Cortex processing returned no result")
        
        result = result_df[0]['PROCESSED_RESULT']
        
        # Get current user and database
        user_df = session.sql("SELECT CURRENT_USER()").collect()
        db_df = session.sql("SELECT CURRENT_DATABASE()").collect()
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
        
        # Log success to database if config_id is provided
        if config_id:
            log_sql = f"""
                INSERT INTO cyphr_execution_logs (config_id, log_level, message)
                VALUES ({config_id}, 'INFO', 'Successfully processed data with Cortex')
            """
            session.sql(log_sql).collect()
        else:
            logger.info("Successfully processed data with Cortex")
            
        return result, response_metadata
        
    except Exception as e:
        error_msg = str(e)
        
        # Log error to database if config_id is provided
        config_id = None
        if metadata:
            config_id = metadata.get("config_id")
            
        if config_id:
            log_sql = f"""
                INSERT INTO cyphr_execution_logs (config_id, log_level, message)
                VALUES ({config_id}, 'ERROR', 'Error processing data with Cortex: {error_msg}')
            """
            session.sql(log_sql).collect()
        else:
            logger.error(f"Error processing data with Cortex: {str(e)}")
            
        raise
