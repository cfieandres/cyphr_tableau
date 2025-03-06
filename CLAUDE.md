# CLAUDE.md - cyphr AI Extension for Tableau

## Project Information
- App Name: cyphr
- Author: Andres Moreno
- Email: mor.qca@gmail.com
- Organization: cyphr

## Build & Run Commands
- Backend: `uvicorn main:app --reload`
- Frontend: `cd tableau-ai-extension && npm run dev`
- Install backend deps: `pip install -r requirements.txt`
- Install frontend deps: `cd tableau-ai-extension && npm install`

## Testing Commands
- Backend tests: `pytest`
- Backend single test: `pytest tests/test_file.py::test_name -v`
- Frontend tests: `cd tableau-ai-extension && npm test`
- Frontend single test: `cd tableau-ai-extension && npm test -- -t "test name"`

## Linting & Formatting
- Python: `flake8` and `black .`
- JavaScript: `cd tableau-ai-extension && npm run lint`

## Code Style Guidelines
- **Python**: PEP 8, type hints, docstrings, imports grouped (stdlib, 3rd-party, local)
- **JavaScript/React**: ES6+, functional components, TypeScript for type safety
- **Error Handling**: Use try/except with specific exceptions in Python, try/catch in JS
- **Naming**: snake_case for Python, camelCase for JS, PascalCase for React components
- **Documentation**: Docstrings for Python functions, JSDoc for JS functions

## General instructions
plans/project_description.md