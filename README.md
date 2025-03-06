# cyphr AI Extension for Tableau

A powerful AI-driven extension for Tableau dashboards that provides analytics, summarization, and general AI assistance using Claude via Snowflake Cortex.

## Overview

The cyphr AI Extension allows Tableau users to interact with AI capabilities directly from their dashboards. The extension retrieves data from Tableau views and processes it using Claude LLM via Snowflake Cortex to provide insights, summaries, and answers to questions.

## Features

- **Analytics**: Get AI-powered insights from your Tableau dashboard data
- **Summarization**: Generate concise summaries of complex datasets
- **General Q&A**: Ask questions about your data and get helpful answers
- **Server Management UI**: Configure AI endpoints and agent settings through a web interface
- **Privacy Protection**: Built-in anonymization of sensitive data (emails, phone numbers, etc.)
- **Response Formatting**: Automatic formatting of responses for better readability

## Architecture

- **Frontend**: React-based extension that embeds in Tableau dashboards
- **Backend**: Python FastAPI server deployed as containers in Snowflake Container Services
- **AI Integration**: Claude LLM via Snowflake Cortex AI functions
- **Data Retrieval**: Tableau REST API and MCP servers

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+
- Snowflake account with Cortex AI enabled
- Tableau Server or Tableau Online account

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/cyphr-ai-extension.git
   cd cyphr-ai-extension
   ```

2. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd tableau-ai-extension
   npm install
   ```

4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
   Update the values in `.env` with your actual settings.

5. Set up Snowflake Cortex AI functions:
   ```
   python setup_cortex.py
   ```

### Running the Server

Start the backend server:

```
uvicorn main:app --reload
```

The server will be available at http://localhost:8000.

### Developing the Frontend

Start the frontend development server:

```
cd tableau-ai-extension
npm run dev
```

The frontend will be available at http://localhost:3000.

### Testing

#### Connectivity Tests
- Test Snowflake connection: `python test_snowflake_connection.py`
- Test Tableau connection: `python test_tableau_connection.py`

#### Component Tests
- Run backend tests: `pytest`
- Run frontend tests: `cd tableau-ai-extension && npm test`
- Run integration tests: `python integration_test.py`
- Run performance tests: `python perf_test.py`
- Run UAT tests: `python uat_test.py`

## Deployment

### Building the Docker Image

```
docker build -t cyphr-ai-extension .
```

### Deploying to Snowflake Container Services

```
# Login to your Snowflake registry
docker login your-snowflake-registry.azurecr.io

# Tag the image
docker tag cyphr-ai-extension your-snowflake-registry.azurecr.io/cyphr-ai-extension:latest

# Push the image
docker push your-snowflake-registry.azurecr.io/cyphr-ai-extension:latest
```

Update `config.yaml` with your specific Snowflake settings and deploy using Snowflake Container Services.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- Author: Andres Moreno
- Email: mor.qca@gmail.com