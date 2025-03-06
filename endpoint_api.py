from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional
import logging

# Import our database
from database.db import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define request models
class EndpointCreate(BaseModel):
    """Model for creating or updating an endpoint."""
    endpoint: str
    agent_id: str
    instructions: str
    name: str
    description: str = ""
    indicators: List[str] = []
    priority: int = 100
    model: str = "claude-3-5-sonnet"
    temperature: float = 0.7

# Create router
router = APIRouter(prefix="/api/endpoints", tags=["endpoints"])

@router.get("")
async def list_endpoints():
    """
    Get all endpoint configurations.
    
    Returns:
        List of all endpoint configurations
    """
    # For debugging
    print("LIST ENDPOINTS API CALLED")
    
    endpoints = db.get_all_endpoints()
    return {"endpoints": endpoints}

@router.get("/{endpoint_path}")
async def get_endpoint(endpoint_path: str):
    """
    Get a specific endpoint configuration.
    
    Args:
        endpoint_path: The endpoint path
        
    Returns:
        The endpoint configuration
    """
    # Ensure the endpoint path starts with a "/"
    if not endpoint_path.startswith('/'):
        endpoint_path = f"/{endpoint_path}"
    
    endpoint = db.get_endpoint(endpoint_path)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint_path}' not found")
    
    return endpoint

@router.post("")
async def create_or_update_endpoint(endpoint_data: EndpointCreate):
    """
    Create or update an endpoint configuration.
    
    Args:
        endpoint_data: The endpoint configuration data
        
    Returns:
        The created or updated endpoint configuration
    """
    try:
        # Log received data for debugging
        logger.info(f"Received endpoint data: {endpoint_data.dict()}")
        
        # Ensure the endpoint path starts with a "/"
        if not endpoint_data.endpoint.startswith('/'):
            endpoint_data.endpoint = f"/{endpoint_data.endpoint}"
        
        # Try to create or update the endpoint
        endpoint = db.add_or_update_endpoint(
            endpoint=endpoint_data.endpoint,
            agent_id=endpoint_data.agent_id,
            instructions=endpoint_data.instructions,
            name=endpoint_data.name,
            description=endpoint_data.description,
            indicators=endpoint_data.indicators,
            priority=endpoint_data.priority,
            model=endpoint_data.model,
            temperature=endpoint_data.temperature
        )
        
        # Check if it was created or updated
        existed = db.get_endpoint(endpoint_data.endpoint) is not None
        status_code = 200 if existed else 201
        
        # Return JSON response
        return {
            "status": "success", 
            "message": f"Endpoint {endpoint_data.endpoint} {'updated' if existed else 'created'} successfully",
            "endpoint": endpoint_data.endpoint
        }
    except Exception as e:
        logger.error(f"Error creating/updating endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create or update endpoint: {str(e)}")

@router.delete("/{endpoint_path}")
async def delete_endpoint(endpoint_path: str):
    """
    Delete an endpoint configuration.
    
    Args:
        endpoint_path: The endpoint path
        
    Returns:
        Success message
    """
    # Ensure the endpoint path starts with a "/"
    if not endpoint_path.startswith('/'):
        endpoint_path = f"/{endpoint_path}"
    
    # Check if the endpoint exists
    if not db.get_endpoint(endpoint_path):
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint_path}' not found")
    
    # Try to delete the endpoint
    deleted = db.delete_endpoint(endpoint_path)
    if not deleted:
        raise HTTPException(status_code=500, detail=f"Failed to delete endpoint '{endpoint_path}'")
    
    return {"status": "success", "message": f"Endpoint '{endpoint_path}' deleted successfully"}