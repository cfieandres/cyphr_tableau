from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, List
from enum import Enum
import uvicorn
import os
from pathlib import Path
import json

# Create the FastAPI app
app = FastAPI(
    title="cyphr AI Extension API",
    description="API for the cyphr AI Extension for Tableau",
    version="1.0.0"
)

app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # For development only! In production, specify exact origins
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
)

# Setup templates directory for the management UI
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR) / "templates"))

# Create static files mount for the management UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Basic endpoints
@app.get("/")
async def root():
    """Root endpoint that returns a message indicating that the server is running."""
    return {"message": "cyphr AI Extension Server is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}

# AI processing endpoints
from process_with_claude import SnowflakeLLMProcessor
from pydantic import BaseModel

class DataRequest(BaseModel):
    """Model for data processing requests."""
    data: str

# Initialize the LLM processor
llm_processor = SnowflakeLLMProcessor()

# Set up logging configuration
import logging
logging.basicConfig(
    level=logging.INFO if os.getenv("CYPHR_DEBUG", "false").lower() == "true" else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from format_response import format_response

class FormatType(str, Enum):
    """Enum for the different types of response formatting."""
    AUTO = "auto"
    BULLET = "bullet"
    PARAGRAPH = "paragraph"
    JSON = "json"
    RAW = "raw"

class AnalyticsRequest(BaseModel):
    """Model for analytics requests with optional format type."""
    data: str
    format_type: FormatType = FormatType.AUTO

from anonymize_data import anonymize_data

@app.post("/analytics")
async def analytics(request: AnalyticsRequest):
    """
    Process data for analytics insights using Claude.
    
    Args:
        request: The request containing data to analyze and format type
        
    Returns:
        JSON response with Claude's analytics
    """
    # Anonymize sensitive data
    anonymized_data = anonymize_data(request.data)
    
    # Try to parse the data to detect if it's combined worksheet data
    try:
        data_obj = json.loads(anonymized_data)
        if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
            # Format the data from multiple worksheets
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
            
            # Create a prompt for analytics with the formatted data
            prompt = f"""Analyze the following Tableau dashboard data and provide comprehensive insights:

{formatted_data}

Provide insights about:
1. Key trends and patterns across worksheets
2. Notable correlations or relationships
3. Anomalies or outliers
4. Potential business implications
5. Suggestions for further analysis

Make your analysis specific and data-driven."""
        else:
            # Regular data format
            prompt = f"Analyze the following data and provide insights:\n\n{anonymized_data}"
    except (json.JSONDecodeError, TypeError):
        # Not valid JSON or not the expected structure, use standard prompt
        prompt = f"Analyze the following data and provide insights:\n\n{anonymized_data}"
    
    # Process with Claude using endpoint-specific configuration
    response = llm_processor.process_query(
        prompt, 
        temperature=0.5,
        endpoint="/analytics",
        agent_config=agent_config_manager
    )
    
    # Format the response
    formatted_response = format_response(response, format_type=request.format_type)
    
    # Return the formatted response
    return {"response": formatted_response}

class SummarizationRequest(BaseModel):
    """Model for summarization requests with optional format type."""
    data: str
    format_type: FormatType = FormatType.PARAGRAPH

@app.post("/summarization")
async def summarization(request: SummarizationRequest):
    """
    Summarize data using Claude.
    
    Args:
        request: The request containing data to summarize and format type
        
    Returns:
        JSON response with Claude's summary
    """
    # Anonymize sensitive data
    anonymized_data = anonymize_data(request.data)
    
    # Try to parse the data to detect if it's combined worksheet data
    try:
        data_obj = json.loads(anonymized_data)
        if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
            # Format the data from multiple worksheets
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
            
            # Create a prompt for summarization with the formatted data
            prompt = f"""Provide a concise summary of the following Tableau dashboard data:

{formatted_data}

Your summary should:
1. Highlight the key information presented in each worksheet
2. Provide an overall perspective on what the dashboard is showing
3. Be clear, concise, and focused on the most important points
4. Use bullet points for clarity where appropriate"""
        else:
            # Regular data format
            prompt = f"Provide a concise summary of the following data:\n\n{anonymized_data}"
    except (json.JSONDecodeError, TypeError):
        # Not valid JSON or not the expected structure, use standard prompt
        prompt = f"Provide a concise summary of the following data:\n\n{anonymized_data}"
    
    # Process with Claude using endpoint-specific configuration
    response = llm_processor.process_query(
        prompt, 
        temperature=0.3,
        endpoint="/summarization",
        agent_config=agent_config_manager
    )
    
    # Format the response
    formatted_response = format_response(response, format_type=request.format_type)
    
    # Return the formatted response
    return {"response": formatted_response}

class GeneralRequest(BaseModel):
    """Model for general requests with optional format type."""
    data: str
    format_type: FormatType = FormatType.AUTO
    question: Optional[str] = None

@app.post("/general")
async def general(request: GeneralRequest):
    """
    Process general queries with Claude.
    
    Args:
        request: The request containing the query data, optional question, and format type
        
    Returns:
        JSON response with Claude's answer
    """
    # Check if the data is a JSON string with a question
    try:
        if isinstance(request.data, str) and request.data.strip().startswith('{'):
            data_obj = json.loads(request.data)
            if isinstance(data_obj, dict) and 'question' in data_obj and 'data' in data_obj:
                # Extract question and data
                question = data_obj['question']
                data = data_obj['data']
                
                # Check if data is the combined worksheets format
                if isinstance(data, dict) and 'worksheets' in data and isinstance(data['worksheets'], list):
                    dashboard_name = data.get('dashboardName', 'Dashboard')
                    formatted_data = f"# {dashboard_name}\n\n"
                    
                    for worksheet in data['worksheets']:
                        ws_name = worksheet.get('name', 'Unnamed Worksheet')
                        ws_data = worksheet.get('data', {})
                        
                        # Format each worksheet section
                        formatted_data += f"## {ws_name}\n"
                        
                        # Convert worksheet data to a readable format
                        ws_data_str = json.dumps(ws_data, indent=2)
                        formatted_data += f"```\n{ws_data_str}\n```\n\n"
                    
                    # Anonymize sensitive data
                    anonymized_data = anonymize_data(formatted_data)
                    
                    # Create a prompt with the question and formatted data
                    prompt = f"""Question: {question}

Dashboard Data:
{anonymized_data}

Please answer the question based solely on the dashboard data provided. Be specific and refer to the worksheet data where relevant. If the question cannot be answered with the available data, explain why."""
                else:
                    # Regular data format, convert to JSON string for anonymization
                    data_str = json.dumps(data, indent=2)
                    anonymized_data = anonymize_data(data_str)
                    prompt = f"Question: {question}\n\nData:\n{anonymized_data}\n\nPlease answer the question using only the data provided."
                
                # Process with Claude using endpoint-specific configuration
                response = llm_processor.process_query(
                    prompt, 
                    temperature=0.7,
                    endpoint="/general",
                    agent_config=agent_config_manager
                )
                
                # Format the response
                formatted_response = format_response(response, format_type=request.format_type)
                
                # Return the formatted response
                return {"response": formatted_response}
    except json.JSONDecodeError:
        # Not a valid JSON string, continue with normal processing
        pass
    except Exception as e:
        logging.error(f"Error processing general request with question: {e}")
    
    # If we get here, process as a normal general request
    
    # If there's an explicit question in the request model
    if request.question:
        anonymized_data = anonymize_data(request.data)
        
        # Try to parse the data to detect if it's combined worksheet data
        try:
            data_obj = json.loads(anonymized_data)
            if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
                # Format the data from multiple worksheets
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
                
                # Create a prompt with the question and formatted data
                prompt = f"""Question: {request.question}

Dashboard Data:
{formatted_data}

Please answer the question based solely on the dashboard data provided. Be specific and refer to the worksheet data where relevant. If the question cannot be answered with the available data, explain why."""
            else:
                # Regular data format
                prompt = f"Question: {request.question}\n\nData:\n{anonymized_data}\n\nPlease answer the question using only the data provided."
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON or not the expected structure, use standard prompt
            prompt = f"Question: {request.question}\n\nData:\n{anonymized_data}\n\nPlease answer the question using only the data provided."
    else:
        # No question, use the data directly as prompt
        anonymized_data = anonymize_data(request.data)
        prompt = anonymized_data
    
    # Process with Claude using endpoint-specific configuration
    response = llm_processor.process_query(
        prompt, 
        temperature=0.7,
        endpoint="/general",
        agent_config=agent_config_manager
    )
    
    # Format the response
    formatted_response = format_response(response, format_type=request.format_type)
    
    # Return the formatted response
    return {"response": formatted_response}

# Server Management UI endpoints
from agent_config import AgentConfig

# Initialize the agent configuration manager
agent_config_manager = AgentConfig()

@app.get("/manage", response_class=HTMLResponse)
async def manage_ui(request: Request):
    """
    Server management UI endpoint.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        HTML response with the management UI
    """
    # Get all agent configurations
    configs = agent_config_manager.get_all_configs()
    
    # Convert to a list for the template
    config_list = [
        {
            "endpoint": endpoint,
            "agent_id": settings.agent_id,
            "instructions": settings.instructions,
            "model": settings.model,
            "temperature": settings.temperature
        }
        for endpoint, settings in configs.items()
    ]
    
    # Render the template
    return templates.TemplateResponse(
        "manage.html", 
        {"request": request, "configs": config_list}
    )

class ConfigureRequest(BaseModel):
    """Model for agent configuration requests."""
    endpoint: str
    agent_id: str
    instructions: str
    model: str = "claude"
    temperature: float = 0.7

@app.post("/manage/configure")
async def configure_agent(request: ConfigureRequest):
    """
    Configure an agent endpoint.
    
    Args:
        request: The configuration request
        
    Returns:
        JSON response with the updated configuration
    """
    # Update the configuration
    settings = agent_config_manager.add_or_update_config(
        endpoint=request.endpoint,
        agent_id=request.agent_id,
        instructions=request.instructions,
        model=request.model,
        temperature=request.temperature
    )
    
    # Return the updated settings
    return {"status": "success", "config": settings.dict()}

# Request routing
from enum import Enum

class TaskType(str, Enum):
    """Enum for the different types of tasks that can be routed."""
    ANALYTICS = "analyze"
    SUMMARIZATION = "summarize"
    GENERAL = "general"

async def route_request(data: str, task_type: TaskType, format_type: FormatType = FormatType.AUTO) -> Dict[str, str]:
    """
    Route a request to the appropriate endpoint based on the task type.
    
    Args:
        data: The data to process
        task_type: The type of task to perform
        format_type: The type of formatting to apply to the response
        
    Returns:
        The response from the endpoint
    """
    # Create the request data
    request_data = {"data": data, "format_type": format_type}
    
    # Try to extract question from data if it's a JSON string
    try:
        # Check if it's a JSON string
        if isinstance(data, str) and data.strip().startswith('{'):
            data_obj = json.loads(data)
            # Check if it contains a question field
            if isinstance(data_obj, dict) and 'question' in data_obj:
                request_data["question"] = data_obj.get('question')
    except (json.JSONDecodeError, TypeError, ValueError):
        # Not a valid JSON or doesn't have the expected structure
        pass
    
    # Route to the appropriate endpoint based on the task type
    if task_type == TaskType.ANALYTICS:
        return await analytics(AnalyticsRequest(**request_data))
    elif task_type == TaskType.SUMMARIZATION:
        return await summarization(SummarizationRequest(**request_data))
    elif task_type == TaskType.GENERAL:
        return await general(GeneralRequest(**request_data))
    else:
        return {"response": f"Unknown task type: {task_type}"}

# Add a new endpoint that takes data, task type, and format type
class RouteRequest(BaseModel):
    """Model for routing requests."""
    data: str
    task_type: TaskType
    format_type: FormatType = FormatType.AUTO
    question: Optional[str] = None

@app.post("/route")
async def route_endpoint(request: RouteRequest):
    """
    Route a request to the appropriate endpoint based on the task type.
    
    Args:
        request: The request containing data, task type, format type, and optional question
        
    Returns:
        The response from the routed endpoint
    """
    # Check if we have a question
    if request.question and request.task_type == TaskType.GENERAL:
        # If we have a question and it's a general request, we need to handle it specially
        try:
            # Parse the data as JSON if it's a string
            data_obj = request.data
            if isinstance(request.data, str):
                try:
                    data_obj = json.loads(request.data)
                except json.JSONDecodeError:
                    # Not valid JSON, use as is
                    pass
            
            # Create a data structure with the question and data
            combined_data = {
                "question": request.question,
                "data": data_obj
            }
            
            # Convert to JSON string
            data_json = json.dumps(combined_data)
            
            # Route the request with the combined data
            return await route_request(data_json, request.task_type, request.format_type)
            
        except Exception as e:
            logging.error(f"Error processing route request with question: {e}")
            # Fall back to standard routing
            return await route_request(request.data, request.task_type, request.format_type)
    else:
        # Standard routing without question
        return await route_request(request.data, request.task_type, request.format_type)

# HTTPS Setup
import ssl

def setup_https():
    """
    Set up HTTPS with a self-signed certificate.
    
    Returns:
        SSL context for HTTPS
    """
    # Check if certificate files exist, otherwise generate them
    cert_file = "cert.pem"
    key_file = "key.pem"
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("Generating self-signed certificate...")
        # Command to generate a self-signed certificate
        # In a production environment, you should use a proper CA-signed certificate
        os.system(f"""
        openssl req -x509 -newkey rsa:4096 -nodes -keyout {key_file} -out {cert_file} -days 365 -subj "/CN=localhost"
        """)
        print(f"Self-signed certificate generated: {cert_file}, {key_file}")
    
    # Create an SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(cert_file, key_file)
    
    return ssl_context

if __name__ == "__main__":
    # Get settings from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    use_https = os.getenv("USE_HTTPS", "false").lower() == "true"
    
    # Force debug to false unless explicitly set in environment
    # This prevents collision with Tableau extension debug flag
    debug = False
    if os.getenv("CYPHR_DEBUG", "false").lower() == "true":
        debug = True
        print("Debug mode enabled via CYPHR_DEBUG environment variable")
    
    # Configure SSL if HTTPS is enabled
    ssl_context = None
    if use_https:
        ssl_context = setup_https()
        print("HTTPS enabled with self-signed certificate")
    
    # Run the application using uvicorn
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=debug,
        ssl_keyfile="key.pem" if use_https else None,
        ssl_certfile="cert.pem" if use_https else None
    )