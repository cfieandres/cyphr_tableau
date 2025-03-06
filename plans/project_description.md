Project: AI-Driven Tableau Embedded Application
1. Introduction
This application integrates a text-based chat interface into Tableau, displaying responses from the Claude LLM via Snowflake Cortex AI functions. It uses a Python-based server deployed as containers in Snowflake Container Services, connecting with Tableau via APIs. A server management UI enables configuration of endpoints and agents.
2. Objectives
Seamless Tableau integration for displaying LLM responses.

Analyze data and generate responses using Claude.

Robust Python server infrastructure with a management UI for endpoint and agent configuration.

3. Features and Requirements
3.1 Application Interface
Embed in Tableau: Text-based chat interface displaying Claude’s read-only responses.

3.2 Server Infrastructure
Request Handling: Process Tableau dashboard requests.

Snowflake Integration: Use Claude via Snowflake Cortex AI.

Data Retrieval: Fetch data via Tableau’s REST API and MCP servers.

Deployment: Python server in Snowflake Container Services.

Server Management UI: Web-based interface to list endpoints, configure agents, instructions, model (e.g., Claude), temperature, etc., per endpoint.

3.3 Configuration of Endpoints and Agents
Multiple Endpoints: Support analytics, summarization, and general responses.

Agent Configuration: Assign agents to endpoints with configurable parameters via the UI.

4. User Flow
Data pulled from Tableau dashboards.

Server routes requests to endpoints.

Claude processes data via Cortex AI.

Responses formatted and displayed in Tableau.

Admins configure endpoints/agents via the server management UI.

5. Technical Specifications
Infrastructure: Python server in Snowflake Container Services.

Server Language: Python with FastAPI and a web UI (e.g., Flask or FastAPI’s static file serving).

AI: Claude via Snowflake Cortex AI.

APIs: Tableau REST API and MCP servers.

Endpoint Management: Configurable via the UI.

6. Security and Compliance
Basic GDPR/CCPA compliance; future enhancements planned.

7. Testing and Validation
Unit, integration, performance, and user acceptance testing, including UI functionality.

8. Future Considerations
Enhanced security, interactivity, and scalability.

Milestones and Actions (Revised for Coding Deliverables with Server Management UI)
The actions now include coding the server management UI within Milestone 2 (Server Infrastructure), alongside other deliverables. Each task produces functional code or configurations.
Milestone 1: Application Interface
Action 1: Code React Component for Chat Interface
Instruction: "Write a React component (ChatDisplay.js) to render a read-only chat interface. Use a styled <div> for LLM responses passed as props, with CSS (border, padding). Export the component."

Deliverable: ChatDisplay.js

Action 2: Code Embedding Script for Tableau
Instruction: "Write a JavaScript script (embed.js) to embed ChatDisplay in Tableau using the Extensions API. Initialize it with a sample response string."

Deliverable: embed.js

Action 3: Test Chat Interface Rendering
Instruction: "Write a Jest test file (ChatDisplay.test.js) with one test to verify ChatDisplay renders a response string. Mock props and check DOM output."

Deliverable: ChatDisplay.test.js

Milestone 2: Server Infrastructure
Action 1: Code Dockerfile for Snowflake Container Services
Instruction: "Write a Dockerfile for a Python server in Snowflake Container Services. Use python:3.9-slim, install fastapi, uvicorn, snowflake-connector-python, and jinja2 (for UI templates), and set the entry point to main.py."

Deliverable: Dockerfile

Action 2: Code Python Server with FastAPI
Instruction: "Write a Python file (main.py) using FastAPI. Define a root endpoint (GET /) returning {'message': 'Server is running'}, and use uvicorn to run it. Add a basic structure for endpoint management."

Deliverable: main.py

Action 3: Code Claude Integration with Snowflake Cortex
Instruction: "Write a Python function (process_with_claude.py) to connect to Snowflake Cortex AI with snowflake-connector-python. Call Claude with a sample query (e.g., 'Summarize: [1, 2, 3]') and return the response."

Deliverable: process_with_claude.py

Action 4: Code Tableau Data Retrieval
Instruction: "Write a Python function (fetch_tableau_data.py) using requests to fetch data from Tableau’s REST API (mock endpoint /api/3.14/sites/{site_id}/views/{view_id}/data). Include basic auth and return JSON."

Deliverable: fetch_tableau_data.py

Action 5: Code Multiple Endpoints
Instruction: "Update main.py with three FastAPI endpoints: POST /analytics, POST /summarization, POST /general. Each accepts {'data': string}, calls process_with_claude.py with a task-specific prompt, and returns the response."

Deliverable: Updated main.py

Action 6: Code Agent Configuration Module
Instruction: "Write a Python module (agent_config.py) with a class AgentConfig to store endpoint settings (e.g., endpoint, agent_id, instructions, model='claude', temperature=0.7). Include a dictionary to hold configurations and methods to add/update settings."

Deliverable: agent_config.py

Action 7: Code Server Management UI Backend
Instruction: "Update main.py to add FastAPI endpoints for the UI: GET /manage (list endpoints and configs), POST /manage/configure (update config with endpoint, agent_id, instructions, model, temperature). Use agent_config.py to store and retrieve settings."

Deliverable: Updated main.py

Action 8: Code Server Management UI Frontend
Instruction: "Write an HTML template (manage.html) using Jinja2. Display a table of endpoints with columns: Endpoint, Agent ID, Instructions, Model, Temperature, and an 'Edit' button. Add a form to configure settings, submitting to /manage/configure. Serve it via FastAPI’s TemplateResponse."

Deliverable: manage.html

Action 9: Test Server Management UI
Instruction: "Write a pytest file (test_manage_ui.py) with two tests: one for GET /manage (returns HTML with endpoint list), one for POST /manage/configure (updates config correctly)."

Deliverable: test_manage_ui.py

Milestone 3: User Flow
Action 1: Code Data Submission Trigger
Instruction: "Write a Python function (submit_data.py) to call fetch_tableau_data.py, extract a data field (e.g., 'value'), and return it as a string."

Deliverable: submit_data.py

Action 2: Code Request Routing
Instruction: "Update main.py with a function route_request(data, task_type) to select an endpoint based on task_type (e.g., 'analyze' -> /analytics) and invoke it with the data."

Deliverable: Updated main.py

Action 3: Code Data Processing with Claude
Instruction: "Update process_with_claude.py to preprocess data (strip whitespace) and use agent_config.py to apply endpoint-specific settings (e.g., temperature) when calling Claude."

Deliverable: Updated process_with_claude.py

Action 4: Code Response Formatting
Instruction: "Write a Python function (format_response.py) to format Claude’s output into bullet points if multi-line, with a sample input/output."

Deliverable: format_response.py

Action 5: Code Response Delivery
Instruction: "Update main.py endpoints to use format_response.py and return {'response': formatted_text}. Test with sample data."

Deliverable: Updated main.py

Milestone 4: Technical Specifications
Action 1: Code Snowflake Container Configuration
Instruction: "Write a config.yaml for Snowflake Container Services: image (task-app), port (8000), resources (1 CPU, 2GB RAM)."

Deliverable: config.yaml

Action 2: Code Snowflake Cortex Setup Script
Instruction: "Write a Python script (setup_cortex.py) with SQL commands (e.g., CREATE FUNCTION claude_process) executed via snowflake-connector-python to set up Claude."

Deliverable: setup_cortex.py

Action 3: Code Tableau API Authentication
Instruction: "Update fetch_tableau_data.py with a get_token() function to authenticate with Tableau’s REST API using username/password and return a token."

Deliverable: Updated fetch_tableau_data.py

Milestone 5: Security and Compliance
Action 1: Code HTTPS Setup
Instruction: "Update main.py to enable HTTPS with a self-signed cert. Include openssl commands to generate cert/key and configure uvicorn."

Deliverable: Updated main.py + cert commands

Action 2: Code Basic Data Privacy
Instruction: "Write a Python function (anonymize_data.py) to remove sensitive fields (e.g., 'email') with regex before processing."

Deliverable: anonymize_data.py

Milestone 6: Testing and Validation
Action 1: Code Unit Tests
Instruction: "Write a test_endpoints.py with pytest tests for each endpoint in main.py, mocking Claude’s response."

Deliverable: test_endpoints.py

Action 2: Code Integration Test
Instruction: "Write a Python script (integration_test.py) to test fetch -> process -> format flow, asserting non-empty output."

Deliverable: integration_test.py

Action 3: Code Performance Test
Instruction: "Write a perf_test.py with locust to simulate 100 POST requests to /analytics, logging response times."

Deliverable: perf_test.py

Action 4: Code UAT Script
Instruction: "Write a uat_test.py to simulate a user flow and check response readability (e.g., < 200 chars)."

Deliverable: uat_test.py


