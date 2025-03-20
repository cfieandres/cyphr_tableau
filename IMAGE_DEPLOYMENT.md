# cyphr AI Extension Image Deployment

This document describes how to build, distribute, and deploy cyphr AI Extension using pre-built Docker images.

## Building Images

To build Docker images for distribution:

```bash
# Navigate to project directory
cd /path/to/aiserv

# Build images using docker-compose
docker-compose build

# Tag images for distribution
docker tag aiserv_backend cyphr/ai-extension-backend:latest
docker tag aiserv_frontend cyphr/ai-extension-frontend:latest

# Push images to Docker Hub or private registry
docker login
docker push cyphr/ai-extension-backend:latest
docker push cyphr/ai-extension-frontend:latest
```

## Deploying with Pre-built Images

### Prerequisites

- Docker and Docker Compose installed
- The deployment package (which includes docker-compose.prod.yml, .env.sample, etc.)

### Deployment Steps

1. Create a `.env` file:

```bash
cp .env.sample .env
```

2. Edit `.env` with your Snowflake credentials and other configuration.

3. Deploy using the production script:

```bash
./deploy_production.sh
```

This script:
- Pulls the latest images from the registry
- Starts the containers with proper configuration
- Displays status information

### Manual Deployment

If you prefer to deploy manually:

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start containers
docker-compose -f docker-compose.prod.yml up -d
```

## Managing the Deployment

### Checking Container Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Viewing Logs

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Stopping the Deployment

```bash
docker-compose -f docker-compose.prod.yml down
```

### Updating to Latest Version

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Customizing the Deployment

### Custom Ports

Edit `docker-compose.prod.yml` to change port mappings:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8080 to your desired port
  
  frontend:
    ports:
      - "80:80"      # Change first 80 to your desired port
```

### Custom Image Registry

If you're using a private registry, modify the image names in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    image: your-registry.com/cyphr/ai-extension-backend:latest
  
  frontend:
    image: your-registry.com/cyphr/ai-extension-frontend:latest
```

## Security Considerations

1. Always use HTTPS in production environments
2. Don't store sensitive credentials in Docker images
3. Use proper authentication for your Docker registry
4. Consider using Docker Secrets for managing credentials
5. Set up proper network isolation in production environments