from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import logging

# Import the database
from database.db import db

# Import the LLM processor
from process_with_claude import SnowflakeLLMProcessor

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
    from format_response import format_response as fr
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
    
    # Handle questions
    if request.question:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Add the user's question to the session if session_id is provided
        if session_id:
            db.add_message(session_id, "user", request.question)
        
        # Try to parse the data as JSON
        try:
            data_obj = json.loads(anonymized_data)
            
            # Format for dashboard data
            if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
                dashboard_name = data_obj.get('dashboardName', 'Dashboard')
                formatted_data = f"# {dashboard_name}\n\n"
                
                for worksheet in data_obj['worksheets']:
                    ws_name = worksheet.get('name', 'Unnamed Worksheet')
                    ws_data = worksheet.get('data', {})
                    
                    # Format each worksheet section
                    formatted_data += f"## {ws_name}\n"
                    
                    # Convert worksheet data to a readable format
                    ws_data_str = json.dumps(ws_data, indent=2)
                    formatted_data += f"```\n{ws_data_str}\n```\n\n"
                
                # Get conversation history if available
                conversation_history = ""
                if session_id:
                    conversation_history = db.get_prompt_context(session_id)
                
                # Create prompt with the question, data, and history
                if conversation_history:
                    prompt = f"""Conversation history:
{conversation_history}

New question: {request.question}

Dashboard Data:
{formatted_data}
"""
                else:
                    prompt = f"""Question: {request.question}

Dashboard Data:
{formatted_data}
"""
            else:
                # Regular data format, convert to JSON string
                data_str = json.dumps(data_obj, indent=2)
                
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
{data_str}
"""
                else:
                    prompt = f"""Question: {request.question}

Data:
{data_str}
"""
        except json.JSONDecodeError:
            # Not valid JSON, use as is
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
{anonymized_data}
"""
            else:
                prompt = f"""Question: {request.question}

Data:
{anonymized_data}
"""
    else:
        # No question, just parse the data
        try:
            # Try to parse as JSON
            data_obj = json.loads(anonymized_data)
            
            # Format for dashboard data
            if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
                dashboard_name = data_obj.get('dashboardName', 'Dashboard')
                formatted_data = f"# {dashboard_name}\n\n"
                
                for worksheet in data_obj['worksheets']:
                    ws_name = worksheet.get('name', 'Unnamed Worksheet')
                    ws_data = worksheet.get('data', {})
                    
                    # Format each worksheet section
                    formatted_data += f"## {ws_name}\n"
                    
                    # Convert worksheet data to a readable format
                    ws_data_str = json.dumps(ws_data, indent=2)
                    formatted_data += f"```\n{ws_data_str}\n```\n\n"
                
                # Use formatted data as prompt
                prompt = formatted_data
            else:
                # Use the original JSON string
                prompt = anonymized_data
        except json.JSONDecodeError:
            # Not valid JSON, use as is
            prompt = anonymized_data
    
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