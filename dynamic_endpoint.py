from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import logging

# Import the database
from database.db import db

# Import the LLM processor
from snowflake_llm_processor import SnowflakeLLMProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM processor
llm_processor = SnowflakeLLMProcessor()

# Format types for responses
class FormatType(str, Enum):
    """Enum for the different types of response formatting."""
    AUTO = "auto"
    BULLET = "bullet"
    PARAGRAPH = "paragraph"
    JSON = "json"
    RAW = "raw"

# Base request model
class DynamicEndpointRequest(BaseModel):
    """Model for dynamic endpoint requests."""
    data: str
    format_type: FormatType = FormatType.AUTO
    question: Optional[str] = None
    session_id: Optional[str] = None

# Response formatter
def format_response(response: str, format_type: FormatType = FormatType.AUTO) -> str:
    """
    Format a response based on the requested format type.
    
    Args:
        response: The raw response to format
        format_type: The type of formatting to apply
        
    Returns:
        The formatted response
    """
    from format_response import format_response as fr, optimize_data
    return fr(response, format_type=format_type)

# Create a router for the dynamic endpoints
router = APIRouter()

@router.post("/{endpoint_path:path}")
async def process_dynamic_endpoint(
    endpoint_path: str,
    request: DynamicEndpointRequest
):
    """
    Dynamic endpoint handler that processes requests based on the endpoint configuration.
    
    Args:
        endpoint_path: The path of the endpoint requested
        request: The request data
        
    Returns:
        JSON response with the processed result
    """
    # Skip API paths
    if endpoint_path.startswith('api/'):
        raise HTTPException(status_code=404, detail=f"Endpoint '/{endpoint_path}' not found")
    # Ensure the endpoint path starts with a "/"
    if not endpoint_path.startswith('/'):
        endpoint_path = f"/{endpoint_path}"
    
    # Look up the endpoint configuration
    endpoint_config = db.get_endpoint(endpoint_path)
    if not endpoint_config:
        logger.error(f"Endpoint not found: {endpoint_path}")
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint_path}' not found")
    
    logger.info(f"Processing request for endpoint: {endpoint_path}")
    
    # Get the session if a session ID is provided
    session_id = request.session_id
    if session_id:
        session = db.get_session(session_id)
        if not session:
            # Create a new session if it doesn't exist
            session, _ = db.get_or_create_session(session_id)
    
    # Data processing logic
    anonymized_data = request.data
    prompt = ""
    
    # Process and optimize the data to reduce token usage
    try:
        # Try to parse the data as JSON
        data_obj = json.loads(anonymized_data)
        
        # Use our optimize_data function to reduce tokens
        logger.info("Optimizing data to reduce token usage")
        formatted_data = optimize_data(data_obj)
    except (json.JSONDecodeError, Exception) as e:
        # Not valid JSON or optimization failed, use as is
        logger.warning(f"Data optimization failed: {str(e)}")
        formatted_data = anonymized_data
    
    # Handle questions
    if request.question:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Add the user's question to the session if session_id is provided
        if session_id:
            db.add_message(session_id, "user", request.question)
        
        # Get conversation history if available
        conversation_history = ""
        if session_id:
            conversation_history = db.get_prompt_context(session_id)
        
        # Create prompt with the question, data, and history
        if conversation_history:
            prompt = f"""Conversation history:
{conversation_history}

New question: {request.question}

Data:
{formatted_data}
"""
        else:
            prompt = f"""Question: {request.question}

Data:
{formatted_data}
"""
    else:
        # No question, just use the formatted data as the prompt
        prompt = formatted_data
    
    # Process with Claude using endpoint-specific configuration
    logger.info(f"Processing with Claude using endpoint: {endpoint_path}")
    
    response = llm_processor.process_query(
        prompt, 
        temperature=endpoint_config['temperature'],
        endpoint=endpoint_path,
        model=endpoint_config['model'],
        instructions=endpoint_config['instructions']
    )
    
    # Format the response
    formatted_response = format_response(response, format_type=request.format_type)
    
    # Add the assistant's response to the session if session_id is provided
    if session_id and formatted_response:
        db.add_message(session_id, "assistant", formatted_response)
    
    # Return the formatted response
    return {
        "response": formatted_response,
        "endpoint": endpoint_path,
        "model": endpoint_config['model'],
        "session_id": session_id
    }