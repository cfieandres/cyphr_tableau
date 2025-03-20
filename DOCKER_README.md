# cyphr AI Extension Docker Deployment

This document describes how to deploy the cyphr AI Extension using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- Git clone of this repository

## Configuration

1. Create a `.env` file in the root directory:

```bash
cp .env.sample .env
```

2. Edit the `.env` file and update the Snowflake credentials and other configuration options:

```
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_ROLE=your_role

# Frontend Configuration
REACT_APP_API_BASE_URL=http://localhost:8000
```

## Deployment

### Build and Start Containers

```bash
docker-compose up -d
```

This command builds and starts both the backend and frontend containers.

### Check Container Status

```bash
docker-compose ps
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Containers

```bash
docker-compose down
```

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Service Endpoints

The backend API provides the following endpoints:

- Health check: http://localhost:8000/health
- API endpoints: http://localhost:8000/endpoints
- Management UI: http://localhost:8000/manage
- Monitoring: http://localhost:8000/monitor

## Data Persistence

Database files are stored in the `database` directory and persisted through Docker volumes.

## Production Deployment Considerations

For production deployments, consider the following:

1. **HTTPS**: Configure HTTPS using a reverse proxy like Nginx or Traefik
2. **Environment-specific configuration**: Use different .env files for development, staging, and production
3. **Container orchestration**: Consider using Kubernetes for more complex deployments
4. **Logging and monitoring**: Implement centralized logging and monitoring solutions
5. **CI/CD**: Set up automated build and deployment pipelines

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues, check:

1. That the database files exist in the `database` directory
2. The permissions on the database files

### Frontend Cannot Connect to Backend

If the frontend cannot connect to the backend:

1. Check that the `REACT_APP_API_BASE_URL` environment variable is set correctly
2. Verify that the backend container is running
3. Ensure ports are correctly mapped in docker-compose.yml

## Container Rebuild

To rebuild the containers after making changes:

```bash
docker-compose build
docker-compose up -d
```