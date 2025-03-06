from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
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

@app.get("/endpoints")
async def list_endpoints():
    """Return information about available API endpoints and their capabilities."""
    # Get all registered agent configurations
    configs = agent_config_manager.get_all_configs()
    
    # Format the endpoints for the response
    endpoints = []
    for endpoint, settings in configs.items():
        # Skip internal endpoints that start with underscore
        if endpoint.startswith('_'):
            continue
            
        # Get the endpoint ID without the leading slash
        endpoint_id = endpoint[1:] if endpoint.startswith('/') else endpoint
        
        # Create the endpoint info
        endpoints.append({
            "id": endpoint_id,
            "name": settings.name,
            "description": settings.description,
            "indicators": settings.indicators,
            "priority": settings.priority
        })
    
    # Sort by priority
    endpoints.sort(key=lambda ep: ep.get("priority", 100))
    
    return {"endpoints": endpoints}

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
    level=logging.INFO,  # Always use INFO level for better visibility
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

# No anonymization needed since all data is internal
# from anonymize_data import anonymize_data

@app.post("/analytics")
async def analytics(request: AnalyticsRequest):
    """
    Process data for analytics insights using Claude.
    
    Args:
        request: The request containing data to analyze and format type
        
    Returns:
        JSON response with Claude's analytics
    """
    # No anonymization needed - data is internal only
    anonymized_data = request.data
    
    # Try to parse the data to detect if it's combined worksheet data
    try:
        data_obj = json.loads(anonymized_data)
        if isinstance(data_obj, dict) and 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
            # Format the data from multiple worksheets
            dashboard_name = data_obj.get('dashboardName', 'Dashboard')
            formatted_data = f"# {dashboard_name}\n\n"
            
            # Add processing notes if available
            if 'processingNotes' in data_obj and isinstance(data_obj['processingNotes'], list):
                formatted_data += "## Processing Notes\n\n"
                for note in data_obj['processingNotes']:
                    formatted_data += f"- {note}\n"
                formatted_data += "\n"
            
            # Add regular worksheets
            for worksheet in data_obj['worksheets']:
                ws_name = worksheet.get('name', 'Unnamed Worksheet')
                ws_data = worksheet.get('data', {})
                
                # Format each worksheet section
                formatted_data += f"## {ws_name}\n"
                
                # Add any notes about the data
                if 'note' in ws_data:
                    formatted_data += f"*{ws_data['note']}*\n\n"
                
                # Convert worksheet data to a readable format
                ws_data_str = json.dumps(ws_data, indent=2)
                formatted_data += f"```\n{ws_data_str}\n```\n\n"
            
            # Add information about excluded worksheets if any
            if 'excludedWorksheets' in data_obj and data_obj['excludedWorksheets']:
                formatted_data += "## Excluded Worksheets (Geographical Data)\n\n"
                formatted_data += "The following worksheets were excluded because they contain geographical data:\n\n"
                
                for excluded in data_obj['excludedWorksheets']:
                    worksheet_name = excluded.get('name', 'Unnamed')
                    reason = excluded.get('reason', 'Contains geographical data')
                    formatted_data += f"- **{worksheet_name}**: {reason}\n"
                
                formatted_data += "\n"
            
            # Create a prompt for analytics with the formatted data
            prompt = f"""Analyze the following Tableau dashboard data and provide comprehensive insights:

{formatted_data}

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
    # No anonymization needed - data is internal only
    anonymized_data = request.data
    
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

{formatted_data}"""
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
                    
                    # Add processing notes if available
                    if 'processingNotes' in data and isinstance(data['processingNotes'], list):
                        formatted_data += "## Processing Notes\n\n"
                        for note in data['processingNotes']:
                            formatted_data += f"- {note}\n"
                        formatted_data += "\n"
                    
                    # Add regular worksheets
                    for worksheet in data['worksheets']:
                        ws_name = worksheet.get('name', 'Unnamed Worksheet')
                        ws_data = worksheet.get('data', {})
                        
                        # Format each worksheet section
                        formatted_data += f"## {ws_name}\n"
                        
                        # Add any notes about the data
                        if 'note' in ws_data:
                            formatted_data += f"*{ws_data['note']}*\n\n"
                        
                        # Check for optimized data structure with constants and column mappings
                        has_optimized_format = 'constants' in ws_data and 'columnMapping' in ws_data
                        
                        if has_optimized_format:
                            # Create a more readable, token-efficient representation
                            formatted_data += "**Column Name Mappings:**\n"
                            for original, short in ws_data.get('columnMapping', {}).items():
                                if original != short:  # Only show actual mappings
                                    formatted_data += f"- `{short}` represents `{original}`\n"
                            formatted_data += "\n"
                            
                            # Add constant values that apply to all rows
                            if ws_data.get('constants'):
                                formatted_data += "**Constant Values (apply to all rows):**\n"
                                for key, value in ws_data.get('constants', {}).items():
                                    formatted_data += f"- `{key}`: {value}\n"
                                formatted_data += "\n"
                            
                            # Add sampling information if data was sampled
                            if ws_data.get('sampling'):
                                sampling = ws_data.get('sampling')
                                formatted_data += f"**Sampling Information:** Showing {sampling.get('sampledRows')} rows out of {sampling.get('totalRows')} total (sampling rate: 1/{sampling.get('samplingRate')})\n\n"
                            
                            # Only show rows, not the full metadata
                            display_data = {
                                "rows": ws_data.get('rows', [])
                            }
                            ws_data_str = json.dumps(display_data, indent=2)
                        else:
                            # Use the original format
                            ws_data_str = json.dumps(ws_data, indent=2)
                        formatted_data += f"```\n{ws_data_str}\n```\n\n"
                    
                    # Add information about excluded worksheets if any
                    if 'excludedWorksheets' in data and data['excludedWorksheets']:
                        formatted_data += "## Excluded Worksheets (Geographical Data)\n\n"
                        formatted_data += "The following worksheets were excluded because they contain geographical data:\n\n"
                        
                        for excluded in data['excludedWorksheets']:
                            worksheet_name = excluded.get('name', 'Unnamed')
                            reason = excluded.get('reason', 'Contains geographical data')
                            formatted_data += f"- **{worksheet_name}**: {reason}\n"
                        
                        formatted_data += "\n"
                    
                    # No anonymization needed - data is internal only
                    anonymized_data = formatted_data
                    
                    # Check if the question is about geographical data
                    geo_question_indicators = ['where', 'location', 'map', 'region', 'geographical', 'geography',
                                              'country', 'city', 'state', 'address', 'place', 'area']
                    
                    is_geo_question = any(indicator in question.lower() for indicator in geo_question_indicators)
                    
                    # Check if we have conversation history from the session
                    conversation_history = ""
                    if isinstance(data_obj, dict) and "conversation_history" in data_obj:
                        conversation_history = data_obj.get("conversation_history", "")
                    
                    # Basic prompt with or without conversation history
                    if conversation_history:
                        # Include conversation history for context continuity
                        prompt = f"""Conversation history:
{conversation_history}

New question: {question}

Dashboard Data:
{anonymized_data}
"""
                    else:
                        # No conversation history, just the question and data
                        prompt = f"""Question: {question}

Dashboard Data:
{anonymized_data}
"""
                    
                    # Add specific instructions based on the question type
                    if is_geo_question:
                        prompt += """Note: Geographical data and map visualizations have been completely excluded. If the question requires location information that isn't visible in the provided data, please explicitly mention this limitation in your answer.

"""
                    
                    prompt += """
"""
                else:
                    # Regular data format, convert to JSON string (no anonymization needed)
                    data_str = json.dumps(data, indent=2)
                    anonymized_data = data_str
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
        anonymized_data = request.data
        
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
        # No question, use the data directly as prompt (no anonymization needed)
        anonymized_data = request.data
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
            "name": settings.name,
            "description": settings.description,
            "indicators": settings.indicators,
            "priority": settings.priority,
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
    name: str
    description: str
    indicators: List[str] = []
    priority: int = 100
    model: str = "claude-3-5-sonnet"
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
        name=request.name,
        description=request.description,
        indicators=request.indicators,
        priority=request.priority,
        model=request.model,
        temperature=request.temperature
    )
    
    # Return the updated settings
    return {"status": "success", "config": settings.dict()}

# Request routing
from enum import Enum

class TaskType(str, Enum):
    """Enum for the different types of tasks that can be routed."""
    AUTO = "auto"  # Automatically determine the task type based on dashboard data
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
    
    # Log the incoming data (anonymized or truncated for privacy)
    try:
        if isinstance(data, str):
            data_size = len(data)
            logging.info(f"Received payload size: {data_size} bytes")
            
            try:
                # Try to parse as JSON to log structure without full content
                data_obj_log = json.loads(data)
                if isinstance(data_obj_log, dict):
                    # Log the keys but not all the values
                    keys_list = list(data_obj_log.keys())
                    logging.info(f"Payload structure: {keys_list}")
                    
                    # Check for specific important fields
                    if 'dashboardName' in data_obj_log:
                        logging.info(f"Dashboard name: {data_obj_log.get('dashboardName')}")
                    if 'question' in data_obj_log:
                        question_preview = data_obj_log.get('question', '')[:50]
                        if len(data_obj_log.get('question', '')) > 50:
                            question_preview += "..."
                        logging.info(f"Question: {question_preview}")
                    if 'worksheets' in data_obj_log and isinstance(data_obj_log['worksheets'], list):
                        worksheet_names = [ws.get('name', 'Unnamed') for ws in data_obj_log['worksheets']]
                        logging.info(f"Worksheets: {worksheet_names}")
            except json.JSONDecodeError:
                # Not JSON, just log length
                logging.info("Payload is not in JSON format")
    except Exception as e:
        logging.error(f"Error logging request data: {e}")
    
    # Auto-determine the task type based on dashboard data if AUTO is specified
    if task_type == TaskType.AUTO:
        logging.info("=== AUTO TASK TYPE DETECTION STARTED ===")
        # Try to parse the data to determine dashboard characteristics
        try:
            # Get all available endpoint configurations
            all_configs = agent_config_manager.get_all_configs()
            logging.info(f"Available endpoints: {list(all_configs.keys())}")
            
            # Create a mapping of endpoint IDs to task types
            endpoint_to_tasktype = {}
            for endpoint, settings in all_configs.items():
                # Remove leading slash and convert to uppercase for TaskType enum
                endpoint_id = endpoint.strip('/').upper()
                if hasattr(TaskType, endpoint_id):
                    endpoint_to_tasktype[endpoint] = getattr(TaskType, endpoint_id)
            
            # Default to ANALYTICS if available, otherwise use the first available endpoint
            default_endpoint = "/analytics"
            if default_endpoint not in endpoint_to_tasktype and endpoint_to_tasktype:
                default_endpoint = next(iter(endpoint_to_tasktype.keys()))
            
            determined_task_type = endpoint_to_tasktype.get(default_endpoint, TaskType.ANALYTICS)
            logging.info(f"Default task type: {determined_task_type.value} (from {default_endpoint})")
            
            # Create a scoring system for each endpoint
            endpoint_scores = {endpoint: 0 for endpoint in all_configs.keys()}
            logging.info("Initial scores: " + ", ".join([f"{ep}: {score}" for ep, score in endpoint_scores.items()]))
            
            # Parse the data
            data_obj = None
            if isinstance(data, str):
                try:
                    data_obj = json.loads(data)
                except json.JSONDecodeError:
                    logging.info("Could not parse data as JSON")
            
            if data_obj and isinstance(data_obj, dict):
                dashboard_text = ""
                score_explanations = {endpoint: [] for endpoint in all_configs.keys()}
                
                # Check if there's a question - gives higher score to general endpoint
                if 'question' in data_obj and data_obj['question']:
                    question_text = data_obj['question']
                    logging.info(f"Question detected: '{question_text[:100]}...' if len > 100")
                    
                    # Give a very strong boost to the general endpoint for questions
                    if "/general" in endpoint_scores:
                        # Much stronger boost to ensure question handling
                        endpoint_scores["/general"] += 100
                        score_explanations["/general"].append("Question present (+100)")
                        logging.info(f"Question detected, strongly boosting /general score (+100)")
                    
                    # Add the question to the dashboard text for keyword matching
                    dashboard_text += question_text + " "
                
                # Add dashboard name to the text
                if 'dashboardName' in data_obj:
                    dashboard_name = data_obj.get('dashboardName', '').lower()
                    dashboard_text += dashboard_name + " "
                    logging.info(f"Dashboard name: {dashboard_name}")
                    
                # Add worksheet names to the text
                worksheet_count = 0
                if 'worksheets' in data_obj and isinstance(data_obj['worksheets'], list):
                    worksheet_count = len(data_obj['worksheets'])
                    worksheet_names = []
                    
                    for ws in data_obj['worksheets']:
                        ws_name = ws.get('name', '').lower()
                        worksheet_names.append(ws_name)
                        dashboard_text += ws_name + " "
                    
                    logging.info(f"Worksheets ({worksheet_count}): {worksheet_names}")
                    
                    # Use number of worksheets as an indicator
                    if worksheet_count <= 2:
                        # For few worksheets, boost summarization score
                        if "/summarization" in endpoint_scores:
                            endpoint_scores["/summarization"] += 10
                            score_explanations["/summarization"].append(f"Few worksheets ({worksheet_count}) (+10)")
                            logging.info(f"Few worksheets ({worksheet_count}), boosting /summarization (+10)")
                    else:
                        # For many worksheets, boost analytics score
                        if "/analytics" in endpoint_scores:
                            endpoint_scores["/analytics"] += 10
                            score_explanations["/analytics"].append(f"Many worksheets ({worksheet_count}) (+10)")
                            logging.info(f"Many worksheets ({worksheet_count}), boosting /analytics (+10)")
                
                # Check for indicators in the dashboard text
                for endpoint, settings in all_configs.items():
                    matching_indicators = []
                    for indicator in settings.indicators:
                        if indicator.lower() in dashboard_text.lower():
                            endpoint_scores[endpoint] += 5
                            matching_indicators.append(indicator)
                    
                    if matching_indicators:
                        score_explanations[endpoint].append(f"Matched indicators: {matching_indicators} (+{len(matching_indicators)*5})")
                        logging.info(f"Endpoint {endpoint} matched indicators: {matching_indicators} (+{len(matching_indicators)*5})")
                
                # Add priority as a base score (inverted, since lower priority number = higher importance)
                for endpoint, settings in all_configs.items():
                    # Max priority is 1000, so we adjust the score inversely
                    priority_score = max(0, (1000 - settings.priority) / 10)
                    endpoint_scores[endpoint] += priority_score
                    score_explanations[endpoint].append(f"Priority {settings.priority} (base: +{priority_score:.1f})")
                    logging.info(f"Endpoint {endpoint} priority {settings.priority} adds base score: +{priority_score:.1f}")
                
                # Log the final scores and explanations
                logging.info("=== ENDPOINT SCORING RESULTS ===")
                for endpoint, score in sorted(endpoint_scores.items(), key=lambda x: x[1], reverse=True):
                    explanation = "; ".join(score_explanations[endpoint])
                    logging.info(f"{endpoint}: {score:.1f} points - {explanation}")
                
                # Select the highest scoring endpoint
                if endpoint_scores:
                    best_endpoint = max(endpoint_scores.items(), key=lambda x: x[1])[0]
                    if best_endpoint in endpoint_to_tasktype:
                        determined_task_type = endpoint_to_tasktype[best_endpoint]
                        logging.info(f"Selected endpoint: {best_endpoint} with task type: {determined_task_type.value}")
            else:
                logging.info("No structured data to analyze for endpoint selection")
            
            # Set the determined task type
            task_type = determined_task_type
            logging.info(f"=== FINAL DECISION: Using task type: {task_type.value} ===")
            
        except Exception as e:
            logging.error(f"Error auto-determining task type: {e}")
            # Default to analytics if error occurs
            task_type = TaskType.ANALYTICS
            logging.info(f"Defaulting to {task_type.value} due to error")
    
    # Route to the appropriate endpoint based on the task type
    logging.info(f"Routing request to task type: {task_type.value}")
    
    if task_type == TaskType.ANALYTICS:
        logging.info("Calling analytics endpoint")
        response = await analytics(AnalyticsRequest(**request_data))
        logging.info(f"Analytics response: {response.get('response', '')[:100]}...")
        # Add the selected endpoint to the response
        response["selected_endpoint"] = "analytics"
        return response
    elif task_type == TaskType.SUMMARIZATION:
        logging.info("Calling summarization endpoint")
        response = await summarization(SummarizationRequest(**request_data))
        logging.info(f"Summarization response: {response.get('response', '')[:100]}...")
        # Add the selected endpoint to the response
        response["selected_endpoint"] = "summarization"
        return response
    elif task_type == TaskType.GENERAL:
        logging.info("Calling general endpoint")
        response = await general(GeneralRequest(**request_data))
        logging.info(f"General response: {response.get('response', '')[:100]}...")
        # Add the selected endpoint to the response
        response["selected_endpoint"] = "general"
        return response
    else:
        logging.error(f"Unknown task type: {task_type}")
        return {"response": f"Unknown task type: {task_type}"}

# Add a new endpoint that takes data, task type, and format type
class RouteRequest(BaseModel):
    """Model for routing requests."""
    data: str
    task_type: TaskType
    format_type: FormatType = FormatType.AUTO
    question: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/route")
async def route_endpoint(request: RouteRequest):
    """
    Route a request to the appropriate endpoint based on the task type.
    
    Args:
        request: The request containing data, task type, format type, optional question,
                and optional session_id
        
    Returns:
        The response from the routed endpoint
    """
    # Import the session manager
    from session_manager import session_manager
    
    # Get or create a session for this request
    session, created = session_manager.get_or_create_session(request.session_id)
    session_id = session.id
    
    # Log the incoming request for debugging
    logging.info(f"Route endpoint request received - Task Type: {request.task_type}, " +
                f"Has Question: {bool(request.question)}, Session ID: {session_id}, New Session: {created}")
    
    # Special handling for requests with questions
    if request.question:
        logging.info(f"Processing request with question: '{request.question[:50]}...' if len > 50")
        
        # Add the user's question to the session history
        session_manager.add_message(session_id, "user", request.question)
        
        try:
            # Parse the data as JSON if it's a string
            data_obj = request.data
            if isinstance(request.data, str):
                try:
                    data_obj = json.loads(request.data)
                except json.JSONDecodeError:
                    # Not valid JSON, use as is
                    logging.warning("Question data is not valid JSON")
                    pass
            
            # Create a data structure with the question, data, and session info
            combined_data = {
                "question": request.question,
                "data": data_obj,
                "session_id": session_id,
                "conversation_history": session.get_prompt_context() if len(session.messages) > 1 else ""
            }
            
            # Convert to JSON string
            data_json = json.dumps(combined_data)
            
            # For AUTO type or explicit GENERAL type, we handle questions
            if request.task_type == TaskType.AUTO:
                logging.info("Auto task type with question - setting task hint for GENERAL endpoint")
                # Use the combined data but hint that this is a question for scoring
                response = await route_request(data_json, TaskType.AUTO, request.format_type)
            else:
                # Use the explicit task type (like GENERAL)
                logging.info(f"Explicit task type {request.task_type} with question")
                response = await route_request(data_json, request.task_type, request.format_type)
            
            # Add the assistant's response to the session history
            session_manager.add_message(session_id, "assistant", response.get("response", ""))
            
            # Add the session ID to the response
            response["session_id"] = session_id
            
            return response
            
        except Exception as e:
            logging.error(f"Error processing route request with question: {e}")
            # Fall back to standard routing
            response = await route_request(request.data, request.task_type, request.format_type)
            response["session_id"] = session_id
            return response
    else:
        # Standard routing without question
        logging.info(f"Standard routing without question, task type: {request.task_type}")
        response = await route_request(request.data, request.task_type, request.format_type)
        response["session_id"] = session_id
        return response

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

# Monitoring and logging endpoints
from request_logs import log_request, get_logs, get_log_by_id, get_stats, estimate_tokens, clear_logs
from fastapi import Request as FastAPIRequest
from fastapi import Depends, HTTPException, Query
from typing import List, Optional, Set
import time

# Middleware for logging requests
@app.middleware("http")
async def log_requests_middleware(request: FastAPIRequest, call_next):
    """Middleware to log requests and responses."""
    # Skip logging for static files and monitoring endpoints
    if request.url.path.startswith("/static") or request.url.path.startswith("/monitor"):
        return await call_next(request)
    
    # Get client IP
    client_host = request.client.host if request.client else None
    
    # Start timing
    start_time = time.time()
    
    # Process the request
    try:
        # Get the request body
        body = await request.body()
        request_data = body.decode() if body else ""
        
        # Process the request
        response = await call_next(request)
        
        # Only log API endpoints
        if (request.url.path.startswith("/analytics") or 
            request.url.path.startswith("/summarization") or 
            request.url.path.startswith("/general") or
            request.url.path.startswith("/route")):
            
            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            
            # Get the response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Decode the response body
            response_data = response_body.decode()
            
            # Try to parse the response as JSON
            response_json = {}
            try:
                import json
                response_json = json.loads(response_data)
            except:
                pass
            
            # Get the model from the response if available
            model = None
            if isinstance(response_json, dict) and "model" in response_json:
                model = response_json.get("model")
            
            # Extract selected endpoint if available
            selected_endpoint = None
            if isinstance(response_json, dict) and "selected_endpoint" in response_json:
                # Properly capture the selected endpoint from the route response
                selected_endpoint = response_json.get("selected_endpoint")
                logging.info(f"Detected routed endpoint: {selected_endpoint}")
            
            # Estimate token counts
            input_tokens = estimate_tokens(request_data)
            output_tokens = estimate_tokens(response_data)
            
            # Log the request
            log_id = log_request(
                endpoint=request.url.path,
                prompt_data=request_data,
                response=response_data,
                selected_endpoint=selected_endpoint,
                execution_time_ms=execution_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                status="success",
                client_ip=client_host
            )
            
            # Create a new response with the same content
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        return response
        
    except Exception as e:
        # Log the error
        execution_time = int((time.time() - start_time) * 1000)
        
        # If we have request data, log it
        if request.url.path.startswith(("/analytics", "/summarization", "/general", "/route")):
            log_request(
                endpoint=request.url.path,
                prompt_data=request_data if 'request_data' in locals() else "",
                response=str(e),
                execution_time_ms=execution_time,
                status="error",
                client_ip=client_host
            )
        
        # Re-raise the exception
        raise

# Monitoring UI endpoints
@app.get("/monitor", response_class=HTMLResponse)
async def monitor_ui(
    request: FastAPIRequest,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    endpoint: Optional[str] = None,
    selected_endpoint: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Monitoring dashboard UI endpoint.
    
    Args:
        request: The FastAPI request object
        limit: Maximum number of logs to return
        offset: Offset for pagination
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        endpoint: Filter by endpoint
        model: Filter by model
        status: Filter by status
        
    Returns:
        HTML response with the monitoring dashboard
    """
    # Get logs with filters
    logs = get_logs(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        endpoint=endpoint,
        selected_endpoint=selected_endpoint,
        model=model,
        status=status
    )
    
    # Get statistics
    stats = get_stats()
    
    # Get unique endpoints, selected_endpoints, and models for filtering
    endpoints = set()
    selected_endpoints = set()
    models = set()
    
    for log in logs:
        if log["endpoint"]:
            endpoints.add(log["endpoint"])
        if log["selected_endpoint"]:
            selected_endpoints.add(log["selected_endpoint"])
        if log["model"]:
            models.add(log["model"])
    
    # Render the template
    return templates.TemplateResponse(
        "monitor.html", 
        {
            "request": request, 
            "logs": logs,
            "stats": stats,
            "limit": limit,
            "offset": offset,
            "endpoints": sorted(endpoints),
            "selected_endpoints": sorted(selected_endpoints),
            "models": sorted(models)
        }
    )

@app.get("/monitor/log/{log_id}")
async def get_log(log_id: int):
    """
    Get a specific log entry by ID.
    
    Args:
        log_id: The ID of the log entry to retrieve
        
    Returns:
        The log entry
    """
    log = get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@app.get("/monitor/stats")
async def get_stats_endpoint():
    """
    Get statistics about the logged requests.
    
    Returns:
        Dictionary containing statistics
    """
    return get_stats()

@app.post("/monitor/clear")
async def clear_logs_endpoint(days_to_keep: int = 30):
    """
    Clear logs older than the specified number of days.
    
    Args:
        days_to_keep: Number of days of logs to keep
        
    Returns:
        Number of logs deleted
    """
    deleted_count = clear_logs(days_to_keep)
    return {"deleted_count": deleted_count}

# Session management endpoints
from session_manager import session_manager

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    
    Args:
        session_id: The session ID
        
    Returns:
        Session information including message history
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.id,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "messages": session.get_messages(),
        "message_count": len(session.messages)
    }

@app.post("/sessions")
async def create_session():
    """
    Create a new session.
    
    Returns:
        The created session information
    """
    session, _ = session_manager.get_or_create_session()
    
    return {
        "session_id": session.id,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat()
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session.
    
    Args:
        session_id: The session ID
        
    Returns:
        Success status
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove the session
    del session_manager.sessions[session_id]
    
    return {"status": "success", "message": f"Session {session_id} deleted"}

@app.post("/sessions/cleanup")
async def cleanup_sessions():
    """
    Clean up expired sessions.
    
    Returns:
        Number of sessions removed
    """
    deleted_count = session_manager.cleanup_expired_sessions()
    return {"deleted_count": deleted_count}

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