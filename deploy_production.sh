#!/bin/bash

# Production deployment script for cyphr AI Extension

# Ensure we have a .env file
if [ ! -f .env ]; then
  echo "Creating .env file from sample..."
  cp .env.sample .env
  echo "Please edit .env file with your credentials before continuing."
  exit 1
fi

# Pull the latest images
echo "Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Check if containers are running
echo "Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "Deployment completed!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo ""
echo "To view logs, run: docker-compose -f docker-compose.prod.yml logs -f"
echo "To stop containers, run: docker-compose -f docker-compose.prod.yml down"